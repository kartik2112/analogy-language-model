import seaborn as sns
import matplotlib.pyplot as plt
import alm
import json
import os
from itertools import product

plt.rcParams.update({"text.usetex": True, "font.family": "sans-serif", "font.sans-serif": ["Helvetica"]})
os.makedirs('./experiments_results/summary/figure_sup', exist_ok=True)
sns.set_theme(style="darkgrid")
TEMPLATES = {
        'is-to-as': "to-as",
        'is-to-what': "to-what",
        'rel-same': 'rel-same',
        'what-is-to': 'what-to',
        'she-to-as': 'she-as',
        'as-what-same': 'as-what'
    }


def plot_box(df):
    df['template_type'] = df['template_type'].apply(lambda x: TEMPLATES[x])
    # data = ['sat', 'u2', 'u4', 'google', 'bats']
    model = ['bert-large-cased', 'gpt2-xl', 'roberta-large']
    df = df.sort_values(by=['model'])
    g = df.groupby(['data'])
    mean_acc = json.loads(g.accuracy.mean().to_json())
    df['accuracy_mean'] = df['data'].apply(lambda x: mean_acc[x])
    df['accuracy'] = df['accuracy'] - df['accuracy_mean']

    def plot(df_, d):
        fig = plt.figure()
        fig.clear()
        plt.xticks(rotation=30)
        ax = sns.boxplot(x='template_type', y='accuracy', data=df_, hue='model', hue_order=model, order=list(TEMPLATES.values()))
        plt.setp(ax.get_legend().get_texts(), fontsize='15')
        ax.set_xlabel(None)
        ax.set_ylabel('Relative Improvement', fontsize=15)
        ax.tick_params(labelsize=15)
        fig = ax.get_figure()
        plt.tight_layout()
        handles, labels = ax.get_legend_handles_labels()
        labels = [
            i.replace('bert-large-cased', 'BERT').replace('roberta-large', 'RoBERTa').replace('gpt2-xl', 'GPT2') for i
            in labels]
        ax.legend(handles=handles, labels=labels, loc='upper right')
        fig.savefig('./experiments_results/summary/figure_sup/box.{}.template_type.png'.format(d))
        plt.close()

    plot(df, 'all')
    # for data_ in data:
    #     df_tmp = df[df.data == data_]
    #     plot(df_tmp, data_)


def plot_heatmap(df):
    data = ['sat', 'u2', 'u4', 'google', 'bats']
    # model = ['roberta-large', 'gpt2-xl']
    # big_group = df.groupby(['data', 'model', 'ppl_based_pmi_alpha', 'negative_permutation_weight']).accuracy.max()

    def plot(d, m, accuracy):
        fig = plt.figure()
        fig.clear()
        accuracy = accuracy - accuracy[0.0][0.0]
        accuracy = accuracy.to_frame()
        accuracy = accuracy.round(1)
        accuracy.reset_index(inplace=True)
        accuracy = accuracy.pivot(index='ppl_based_pmi_alpha', columns='negative_permutation_weight', values='accuracy')
        accuracy = accuracy.reindex([0.4, 0.2, 0.0, -0.2, -0.4])
        sns_plot = sns.heatmap(accuracy, annot=True, fmt="g", cbar=False, annot_kws={"fontsize": 15})
        sns_plot.set_xlabel(r'$\beta$', fontsize=18)
        sns_plot.set_ylabel(r'$\alpha$', fontsize=18)
        sns_plot.tick_params(labelsize=15)
        fig = sns_plot.get_figure()
        plt.tight_layout()
        fig.savefig('./experiments_results/summary/figure_sup/heatmap.alpha_beta.{}.{}.png'.format(d, m))
        plt.close()

    # plot('all', 'all', df.groupby(['ppl_based_pmi_alpha', 'negative_permutation_weight']).accuracy.mean())
    # for m_ in model:
    #     plot('all', m_, df.groupby(['model', 'ppl_based_pmi_alpha', 'negative_permutation_weight']).accuracy.mean()[m_])
    #
    for d_ in data:
        plot(d_, 'all', df.groupby(['data', 'ppl_based_pmi_alpha', 'negative_permutation_weight']).accuracy.mean()[d_])

    # for d_, m_ in product(data, model):
    #     plot(d_, m_, big_group[d_][m_])


if __name__ == '__main__':
    dataframe = alm.get_report(export_prefix='experiment.ppl_variants')
    dataframe['accuracy'] = dataframe['accuracy'].round(3) * 100

    # plot_heatmap(dataframe)
    dataframe = dataframe[dataframe.scoring_method == 'ppl_marginal_bias']
    plot_box(dataframe)
