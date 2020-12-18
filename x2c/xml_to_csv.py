import copy

from lxml import etree, html


class Line:
    def __init__(self, size, allowed_duplicates):
        self.size = size
        self.allowed_duplicates = allowed_duplicates
        self.values = [''] * size
        self.prev_values = None
        self.obligatory_elements = [False] * (self.size - self.allowed_duplicates)
        self.yield_queue = None

    def line_yield(self):
        yiel = self.yield_queue
        self.yield_queue = None
        return yiel

    def merge_line(self, new_line):
        for i in range(self.size):
            if i < self.allowed_duplicates and new_line.values[i] != '':
                self.values[i] = new_line.values[i]
            elif i >= self.allowed_duplicates and new_line.values[i] != '' and self.values[i] != '':
                self.yield_queue = self.values
                self.values = self.values[:self.allowed_duplicates] + ([''] * (self.size - self.allowed_duplicates))
                self.obligatory_elements = [False] * (self.size - self.allowed_duplicates)
                self.values[i] = new_line.values[i]
                self.obligatory_elements[i - self.allowed_duplicates] = True
            elif i >= self.allowed_duplicates and new_line.values[i] != '' and self.values[i] == '':
                self.values[i] = new_line.values[i]
                self.obligatory_elements[i - self.allowed_duplicates] = True
            else:
                print('wAAAatHHH??')



    def __call__(self, ind, value):
        if ind < self.allowed_duplicates:
            self.values[ind] = value
            self.obligatory_elements = [False] * (self.size - self.allowed_duplicates)
        else:
            if self.obligatory_elements[ind - self.allowed_duplicates]:
                yield self.values
                # restart values
                self.prev_values = copy.copy(self.values)
                self.values = self.values[:self.allowed_duplicates] + ([''] * (self.size - self.allowed_duplicates))
                self.obligatory_elements = [False] * (self.size - self.allowed_duplicates)
            self.values[ind] = value
            self.obligatory_elements[ind - self.allowed_duplicates] = True


class X2c:
    def __init__(self, path, commands):
        '''
        :param xml:
        Path to xml file.

        :param commands:
        A list of extraction commands, listed as dictionary like a following example:
            example_commands = {
                'column1': {'structure': 'body/div/element', 'print': 'attribute1', 'allow_duplicating': True},
                'column2': {'structure': 'body/div/element/part', 'print': 'text', 'allow_duplicating': False}
            }
        '''
        self.path = path
        self.size = len(commands)
        self.duplicate_shuffle = {}
        shuffeled_commands = {}
        shuffle_i = 0
        for i, (command_k, command_v) in enumerate(commands.items()):
            if 'allow_duplicating' in command_v and command_v['allow_duplicating']:
                self.duplicate_shuffle[i] = shuffle_i
                shuffeled_commands[command_k] = command_v
                shuffle_i += 1

        self.allowed_duplicates = len(shuffeled_commands)

        self.line = Line(self.size, self.allowed_duplicates)

        for i, (command_k, command_v) in enumerate(commands.items()):
            if 'allow_duplicating' not in command_v or not command_v['allow_duplicating']:
                self.duplicate_shuffle[i] = shuffle_i
                shuffeled_commands[command_k] = command_v
                shuffle_i += 1

        path_intersection = None
        for k, v in commands.items():
            struct_split = v['structure'].split('/')
            if path_intersection is None:
                path_intersection = struct_split
            else:
                for i, el in enumerate(struct_split):
                    if i >= len(path_intersection):
                        break
                    if path_intersection[i] != el:
                        path_intersection = path_intersection[:i]
                        break

        self.path_intersection = path_intersection

        actions = {}
        for k_i, (k, v) in enumerate(commands.items()):
            struct_split = v['structure'].split('/')
            if len(struct_split) == len(path_intersection):
                actions.setdefault('prints', []).append(v['print'])
            cur_action = actions
            for i, el in enumerate(struct_split):
                # add to actions only after path intersection
                if i >= len(path_intersection):
                    # add explorable paths to structure
                    cur_action.setdefault('structure', {}).setdefault(struct_split[i], {})
                    cur_action = cur_action['structure'][struct_split[i]]

                    # when in end node add action
                    if i == len(struct_split) - 1:
                        del v['structure']
                        v['id'] = k_i
                        cur_action.setdefault('actions', []).append(v)

        self.actions = actions

    def merge_dicts(self, dict_o, dict_n, allow_duplicates=False):
        # fill blanks
        if allow_duplicates:
            # find max length of dict_o
            max_len = max([len(v) for k, v in dict_o.items()])
            # duplicate value as many times as necessary
            for k_n, v_n in dict_n.items():
                assert len(v_n) == 1
                dict_o[k_n][max_len] = v_n[0]

        else:
            # find max length of dict_o
            max_len = max([len(v) for k, v in dict_o.items()])

            for k_n, v_n in dict_n.items():
                dict_o.setdefault(k_n, {})
                dict_o[k_n] = {**dict_o[k_n], **v_n}

        return dict_o

    def intersection_walk(self, tree, i):
        for tag in tree.iter(self.path_intersection[i]):
            if i + 1 < len(self.path_intersection):
                yield from self.intersection_walk(tag, i + 1)
            else:
                yield from self.walk(tag, self.actions)
                yield copy.copy(self.line.values)

    def walk(self, tree, actions):
        if 'actions' in actions:
            for action in actions['actions']:
                if 'attrib_restrictions' in action:
                    pass_restrictions = True
                    for att_name, att_value in action['attrib_restrictions'].items():
                        if tree.attrib[att_name] != att_value:
                            pass_restrictions = False
                    if not pass_restrictions:
                        continue

                if action['print'] == 'text':
                    yield from self.line(action['id'], tree.text)
                elif action['print'] == 'object':
                    yield from self.line(action['id'], tree)
                else:
                    if action['print'] in tree.attrib:
                        yield from self.line(action['id'], tree.attrib[action['print']])
                    else:
                        yield from self.line(action['id'], '')

        if 'structure' in actions:
            for struct_key, structure_dict in actions['structure'].items():
                for tag in tree.iter(struct_key):
                    yield from self.walk(tag, actions['structure'][struct_key])

    def generator(self):
        tree = etree.parse(self.path)

        yield from self.intersection_walk(tree, 0)

    def to_list(self, func=None):
        if func is not None:
            return [func(r) for r in self.generator()]

        return list(self.generator())
