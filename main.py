import csv
import os

from lxml import html, etree

from x2c.writer import write_csv
from x2c.xml_to_csv import X2c



def decypher_objects_statistics(inp):
    if inp[1] == '':
        inp[2] = ''
    return inp

def decypher_objects_patterns(inp):
    # TODO FIX THIS PRETTIER!
    if inp[1] == '':
        inp[2] = ''

    # form Semantic role
    semantic_roles_list = []
    for sem_rol in inp[5].findall('semanticRoleContainer'):
        semantic_roles_list.append(sem_rol.find('semanticRole').text)
    inp[5] = '_'.join(semantic_roles_list)

    # form corpus example
    if inp[7] is not None and inp[7].find('exampleContainer') is not None:
        corpus_example_text = html.tostring(inp[7].find('exampleContainer').find('corpusExample'), encoding='unicode')
    else:
        print(inp)
        return inp

    # ugly postprocessing to remove xmlns:xsi=... duh..
    root = etree.fromstring(corpus_example_text)

    # Remove namespace prefixes
    for elem in root.getiterator():
        elem.tag = etree.QName(elem).localname
    # Remove unused namespace declarations
    etree.cleanup_namespaces(root)

    inp[7] = etree.tostring(root, encoding='unicode')

    return inp


if __name__ == '__main__':
    commands_gf = {
        'Lemma': {'structure': 'entry/head/headword/lemma', 'print': 'text', 'allow_duplicating': True},
        'LU id': {'structure': 'entry/head/lexicalUnit', 'print': 'id', 'allow_duplicating': True},
        'Grammar': {'structure': 'entry/head/grammar/grammarFeature', 'print': 'text', 'allow_duplicating': True},
        'Semantic role': {'structure': 'entry/body/statisticsContainerList/statisticsContainer/semanticRole', 'print': 'text', 'allow_duplicating': False},
        'Valency pattern ratio gf': {'structure': 'entry/body/statisticsContainerList/statisticsContainer/measureList/measure', 'print': 'text', 'allow_duplicating': False, 'attrib_restrictions': {'type': 'valency_pattern_ratio', 'source': 'Gigafida 2.0'}},
        'Valency sentence ratio gf': {'structure': 'entry/body/statisticsContainerList/statisticsContainer/measureList/measure', 'print': 'text', 'allow_duplicating': False, 'attrib_restrictions': {'type': 'valency_sentence_ratio', 'source': 'Gigafida 2.0'}},
        'Valency pattern ratio ssj': {
            'structure': 'entry/body/statisticsContainerList/statisticsContainer/measureList/measure', 'print': 'text',
            'allow_duplicating': False,
            'attrib_restrictions': {'type': 'valency_pattern_ratio', 'source': 'ssj500k 2.2'}},
        'Valency sentence ratio ssj': {
            'structure': 'entry/body/statisticsContainerList/statisticsContainer/measureList/measure', 'print': 'text',
            'allow_duplicating': False,
            'attrib_restrictions': {'type': 'valency_sentence_ratio', 'source': 'ssj500k 2.2'}}
    }
    commands_patterns = {
        'Lemma': {'structure': 'entry/head/headword/lemma', 'print': 'text', 'allow_duplicating': True},
        'LU id': {'structure': 'entry/head/lexicalUnit', 'print': 'id', 'allow_duplicating': True},
        'Grammar': {'structure': 'entry/head/grammar/grammarFeature', 'print': 'text', 'allow_duplicating': True},
        'Valency pattern id': {'structure': 'entry/body/senseList/sense/valencyPatternList/valencyPattern', 'print': 'id', 'allow_duplicating': False},
        'Frequency all GF': {'structure': 'entry/body/senseList/sense/valencyPatternList/valencyPattern/measureList/measure', 'print': 'text', 'allow_duplicating': False, 'attrib_restrictions': {'type': 'frequency_all', 'source': 'Gigafida 2.0'}},
        'Semantic role': {'structure': 'entry/body/senseList/sense/valencyPatternList/valencyPattern/semanticRoleContainerList', 'print': 'object', 'allow_duplicating': False},
        'Pattern representation': {'structure': 'entry/body/senseList/sense/valencyPatternList/valencyPattern/patternRepresentation', 'print': 'text', 'allow_duplicating': False},
        'Corpus example': {'structure': 'entry/body/senseList/sense/valencyPatternList/valencyPattern/exampleContainerList', 'print': 'object', 'allow_duplicating': False}
    }



    inpt = '/home/luka/Desktop/TEMP_VALENCY/output_temp'
    outpt = 'data/csvs'
    res_gf = []
    res_ssj = []
    res_patterns = []
    for file in sorted(os.listdir(inpt)):
        path = os.path.join(inpt, file)
        x2c_gf = X2c(path, commands_gf)
        x2c_patterns = X2c(path, commands_patterns)
        res_gf.extend(x2c_gf.to_list(decypher_objects_statistics))
        res_patterns.extend(x2c_patterns.to_list(decypher_objects_patterns))

    write_csv(os.path.join(outpt, 'all_statistics.tsv'), res_gf, commands_gf)
    write_csv(os.path.join(outpt, 'all_patterns.tsv'), res_patterns, commands_patterns)
