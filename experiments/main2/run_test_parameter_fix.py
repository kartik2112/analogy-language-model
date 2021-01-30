""" Fix either of 'negative_permutation_weight', 'ppl_pmi_alpha' to see the effect """
import logging
import json
from itertools import product
logging.basicConfig(format='%(asctime)s %(levelname)-8s %(message)s', level=logging.INFO, datefmt='%Y-%m-%d %H:%M:%S')
import alm

data = ['sat', 'u2', 'u4', 'google', 'bats']
models = [('roberta-large', 32, 512), ('gpt2-xl', 32, 128), ('bert-large-cased', 32, 1024)]
export_prefix = 'main2'
df = alm.get_report(export_prefix=export_prefix)

for i, m in product(data, models):
    _model, _len, _batch = m
    tmp_df = df[df.data == i]
    tmp_df = tmp_df[tmp_df.model == _model]
    for p in ['negative_permutation_weight', 'ppl_pmi_alpha']:
        tmp_df_ = tmp_df[tmp_df[p] == 0]
        val_accuracy = tmp_df_.sort_values(by='accuracy', ascending=False).head(1)['accuracy'].values[0]
        logging.info("RUN TEST:\n - data: {} \n - lm: {} \n - validation accuracy: {} ".format(i, _model, val_accuracy))
        best_configs = tmp_df[tmp_df['accuracy'] == val_accuracy]
        logging.info("find {} configs with same accuracy".format(len(best_configs)))
        for n, tmp_df in best_configs.iterrows():
            config = json.loads(tmp_df.to_json())
            config.pop('accuracy')
            config.pop('max_length')
            scorer = alm.RelationScorer(model=config.pop('model'), max_length=_len)
            scorer.analogy_test(test=True,
                                export_prefix=export_prefix,
                                batch_size=_batch,
                                **config)
            scorer.release_cache()
            # compute onl the first one to reduce time
            break

alm.export_report(export_prefix=export_prefix + '.parameter_fix', test=True)
