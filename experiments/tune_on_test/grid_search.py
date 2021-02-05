import alm

all_templates = ['is-to-what', 'is-to-as', 'rel-same', 'what-is-to', 'she-to-as', 'as-what-same']
data = ['sat']
# models = [('roberta-large', 32, 512)]
# models = [('gpt2-xl', 32, 256)]
models = [('bert-large-cased', 32, 1024)]
positive_permutation_aggregation = ['max', 'mean', 'min', 'index_0', 'index_1', 'index_2', 'index_3', 'index_4',
                                    'index_5', 'index_6', 'index_7']
negative_permutation_aggregation = ['max', 'mean', 'min', 'index_0', 'index_1', 'index_2', 'index_3', 'index_4',
                                    'index_5', 'index_6', 'index_7', 'index_8', 'index_9', 'index_10', 'index_11']
ppl_pmi_aggregation = ['max', 'mean', 'min', 'index_0', 'index_1']
ppl_pmi_alpha = [-0.4, -0.2, 0, 0.2, 0.4]
negative_permutation_weight = [0, 0.2, 0.4, 0.6, 0.8, 1.0]
export_prefix = 'tune_on_test'

for _model, _max_length, _batch in models:
    scorer = alm.RelationScorer(model=_model, max_length=_max_length)
    for _data in data:
        for _temp in all_templates:
            for ppl_pmi_marginal_version in [True, False]:
                scorer.analogy_test(
                    test=True,
                    ppl_pmi_marginal_version=ppl_pmi_marginal_version,
                    scoring_method='ppl_pmi',
                    data=_data,
                    template_type=_temp,
                    batch_size=_batch,
                    export_prefix=export_prefix,
                    ppl_pmi_aggregation=ppl_pmi_aggregation,
                    ppl_pmi_alpha=ppl_pmi_alpha,
                    negative_permutation=True,
                    positive_permutation_aggregation=positive_permutation_aggregation,
                    negative_permutation_aggregation=negative_permutation_aggregation,
                    negative_permutation_weight=negative_permutation_weight
                )
                scorer.release_cache()



alm.export_report(export_prefix=export_prefix, test=True)
