import logging
import json
import alm
import pandas as pd

SKIP_INFERENCE = True  # skip inference step
SKIP_GRID_SEARCH = False  # skip grid search
SKIP_MERGE = False  # skip merging result
SKIP_EXPORT_PREDICTION = False  # skip export prediction

logging.basicConfig(format='%(asctime)s %(levelname)-8s %(message)s', level=logging.INFO, datefmt='%Y-%m-%d %H:%M:%S')
logging.info('')
alm.util.fix_seed(1234)
all_templates = ['is-to-what', 'is-to-as', 'rel-same', 'what-is-to', 'she-to-as', 'as-what-same']
data = ['sat']
models = [('roberta-large', 32, 512), ('gpt2-xl', 32, 256), ('bert-large-cased', 32, 1024)]
scoring_method = ['ppl_marginal_bias']
export_prefix = 'experiment.ppl_variants'

if not SKIP_INFERENCE:
    logging.info('###############################################################')
    logging.info('# Run LM inference to get logit (both of valid and test sets) #')
    logging.info('###############################################################')
    no_inference = False
    for _model, _max_length, _batch in models:
        scorer = alm.RelationScorer(model=_model, max_length=_max_length)
        for _data in data:
            for _temp in all_templates:
                for test in [True]:
                    for score in scoring_method:
                        if 'gpt' in _model and score == 'ppl_hypothesis_bias':
                            continue
                        scorer.analogy_test(
                            scoring_method=score,
                            data=_data,
                            template_type=_temp,
                            batch_size=_batch,
                            no_inference=no_inference,
                            negative_permutation=False,
                            skip_scoring_prediction=True,
                            test=test
                        )
                        scorer.release_cache()

if not SKIP_GRID_SEARCH:
    logging.info('######################################################################')
    logging.info('# Get prediction on each configuration (both of valid and test sets) #')
    logging.info('######################################################################')
#     positive_permutation_aggregation = [
#         'max', 'mean', 'min', 'index_0', 'index_1', 'index_2', 'index_3', 'index_4', 'index_5', 'index_6', 'index_7'
#     ]
    positive_permutation_aggregation = {
        'roberta-large': ['index_5'],
        'gpt2-xl': ['index_3'],
        'bert-large-cased': ['index_5']
    }
#     negative_permutation_aggregation = [
#         'max', 'mean', 'min', 'index_0', 'index_1', 'index_2', 'index_3', 'index_4', 'index_5', 'index_6', 'index_7',
#         'index_8', 'index_9', 'index_10', 'index_11'
#     ]
    negative_permutation_aggregation = {
        'roberta-large': ['index_11'],
        'gpt2-xl': ['index_1'],
        'bert-large-cased': ['index_5']
    }
#     negative_permutation_weight = [0, 0.2, 0.4, 0.6, 0.8, 1.0]
    negative_permutation_weight = {
        'roberta-large': [0.2],
        'gpt2-xl': [0.8],
        'bert-large-cased': [0.2]
    }
#     weight_head = [-0.4, -0.2, 0, 0.2, 0.4]
    weight_head = {
        'roberta-large': [0.2],
        'gpt2-xl': [-0.4],
        'bert-large-cased': [-0.2]
    }
#     weight_tail = [-0.4, -0.2, 0, 0.2, 0.4]
    weight_tail = {
        'roberta-large': [0.2],
        'gpt2-xl': [0.2],
        'bert-large-cased': [-0.4]
    }
    ppl_based_pmi_aggregation = ['max', 'mean', 'min', 'index_0', 'index_1']
    ppl_based_pmi_alpha = [-0.4, -0.2, 0, 0.2, 0.4]
    all_templates = {
        'roberta-large': ['as-what-same'],
        'gpt2-xl': ['rel-same'],
        'bert-large-cased': ['what-is-to']
    }
    no_inference = True

    for _model, _max_length, _batch in models:
        scorer = alm.RelationScorer(model=_model, max_length=_max_length)
        for _data in data:
            for _temp in all_templates[_model]:
                for test in [True]:
                    for score in scoring_method:
                        if 'gpt' in _model and score == 'ppl_hypothesis_bias':
                            continue
                        scorer.analogy_test(
                            no_inference=no_inference,
                            scoring_method=score,
                            data=_data,
                            template_type=_temp,
                            batch_size=_batch,
                            export_prefix=export_prefix,
                            ppl_hyp_weight_head=weight_head[_model],
                            ppl_hyp_weight_tail=weight_tail[_model],
                            ppl_mar_weight_head=weight_head[_model],
                            ppl_mar_weight_tail=weight_tail[_model],
                            ppl_based_pmi_aggregation=ppl_based_pmi_aggregation,
                            ppl_based_pmi_alpha=ppl_based_pmi_alpha,
                            negative_permutation=True,
                            positive_permutation_aggregation=positive_permutation_aggregation[_model],
                            negative_permutation_aggregation=negative_permutation_aggregation[_model],
                            negative_permutation_weight=negative_permutation_weight[_model],
                            test=test)
                        scorer.release_cache()

    alm.export_report(export_prefix=export_prefix)
    alm.export_report(export_prefix=export_prefix, test=True)

if not SKIP_MERGE:
    logging.info('####################################')
    logging.info('# Merge validation and test result #')
    logging.info('####################################')
    df_val = alm.get_report(export_prefix=export_prefix)
    df_val = df_val.sort_values(by=list(df_val.columns))

    df_test = alm.get_report(export_prefix=export_prefix, test=True)
    df_test = df_test.sort_values(by=list(df_val.columns))

    accuracy_val = df_val.pop('accuracy').to_numpy()
    accuracy_test = df_test.pop('accuracy').to_numpy()
    assert df_val.shape == df_test.shape

    df_test['accuracy_validation'] = accuracy_val
    df_test['accuracy_test'] = accuracy_test

    summary = {}

    for d in data:
        df_test_ = df_test[df_test.data == d]
        val, test = alm.get_dataset_raw(d)
        df_test_['accuracy'] = (df_test_['accuracy_validation'] * len(val) + df_test_['accuracy_test'] * len(test)) / (len(val) + len(test))
        df_test_ = df_test_.sort_values(by=['accuracy'], ascending=False)
        df_test_.to_csv('./experiments_results/summary/{}.full.{}.csv'.format(export_prefix, d))
        logging.info('Top 3 in {}'.format(d))
        logging.info('\n{}'.format(df_test_['accuracy'].head(3)))
        summary[d] = {}
        for m, _, _ in models:
            df_test__ = df_test_[df_test_['model'] == m]
            acc_full = float(df_test__.sort_values(by=['accuracy'], ascending=False)['accuracy'].head(1))
            acc_val = float(df_test__.sort_values(by=['accuracy_validation'], ascending=False)['accuracy'].head(1))
            summary[d][m] = {'full': acc_full, 'validation': acc_val}
    with open('./experiments_results/summary/{}.top.json'.format(export_prefix), 'w') as f:
        json.dump(summary, f)

if not SKIP_EXPORT_PREDICTION:
    logging.info('###############################################')
    logging.info('# Export predictions for qualitative analysis #')
    logging.info('###############################################')
    # get prediction of what achieves the best validation accuracy
    methods = ['ppl_marginal_bias', 'ppl_hypothesis_bias', 'ppl_based_pmi']
    for d in data:
        logging.info('DATASET: {}'.format(d))
        df_test_full = pd.read_csv('./experiments_results/summary/{}.full.{}.csv'.format(export_prefix, d),
                                   index_col=0)
        for method in methods:
            df_test = df_test_full[df_test_full.scoring_method == method]
            for _model, _max_length, _batch in models:
                df_tmp = df_test[df_test.model == _model]
                df_tmp = df_tmp.sort_values(by=['accuracy_validation'], ascending=False)
                if len(df_tmp) == 0:
                    continue
                acc_val = list(df_tmp.head(1)['accuracy_validation'])[0]
                acc = df_tmp[df_tmp.accuracy_validation == acc_val].sort_values(by=['accuracy_test'])
                acc_test = list(acc['accuracy_test'])
                acc_test = acc_test[int(len(acc_test) / 2)]
                best_configs = df_tmp[df_tmp.accuracy_test == acc_test]
                config = json.loads(best_configs.iloc[0].to_json())
                logging.info("* {}/{}".format(method, _model))
                logging.info("\t * accuracy (valid): {}".format(config.pop('accuracy_validation')))
                logging.info("\t * accuracy (test) : {}".format(config.pop('accuracy_test')))
                logging.info("\t * accuracy (full) : {}".format(config.pop('accuracy')))
                scorer = alm.RelationScorer(model=config.pop('model'), max_length=config.pop('max_length'))
                scorer.analogy_test(test=True, export_prediction=True, no_inference=True, export_prefix=export_prefix,
                                    **config)
                scorer.release_cache()

