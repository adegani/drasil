import copy
import logging
import os.path
from datetime import datetime
import operator
from .drasil_plugins import DrasilPlugin
from .drasil_context import DrasilContext

MAX_MENU_ENTRY = 10

ASSETS_FOLDER = 'assets'

IGNORE_MARKER = '_'
NO_LINK_MARKER = '$'
ORDER_BY_DATE_MARKER = '%'
LEFT_HOOK_MARKER = '[$'
RIGHT_HOOK_MARKER = '$]'


class DrasilBifrost(object):
    def __init__(self, plugins=None):
        super(DrasilBifrost, self).__init__()
        DrasilBifrost.tot_steps = 0

        self.plugins = plugins
        self.src_root = None
        self.output_dir = None
        self.current_node = None
        self.current_level = 0

        self.parent = None
        self.brothers = []
        self.uncles = []
        self.childs = []

        self.template = None

    def walk(self):
        bifrost = self
        DrasilBifrost.tot_steps += 1
        root = bifrost.current_node
        level = bifrost.current_level

        bifrost.current_level += 1
        bifrost.childs = []
        bifrost.brothers = [n for n in os.listdir(root)
                            if n[0] != IGNORE_MARKER if n[0] != '.'
                            if os.path.split(n)[-1] != ASSETS_FOLDER
                            if os.path.split(n)[-1] != 'index.html'
                            if os.path.split(n)[-1] != 'index.htm'
                            if os.path.split(n)[-1] != self._short_name() + '.html'
                            if os.path.split(n)[-1] != self._short_name()[3:] + '.html'
                            if os.path.split(n)[-1] != self._short_name()[1:] + '.html'
                            ]

        if level == 0:
            print('+')
        print('='*(level+1))

        for node in os.listdir(root):
            # print('NODE: %s' % node)
            if node[0] == IGNORE_MARKER or node[0] == '.' or node == ASSETS_FOLDER:
                continue

            new_path = os.path.join(root, node)
            bifrost.current_node = new_path
            if os.path.isfile(new_path):
                print('|'*(level+1))
            if os.path.isdir(new_path):

                step = copy.deepcopy(bifrost)
                step.parent = new_path

                if step.brothers not in step.uncles:
                    step.uncles.append(step.brothers)
                step.walk()

            str_tpl = (bifrost._rel_path(), ', '.join(bifrost.brothers))

            if os.path.isdir(new_path):
                bifrost.childs = [n for n in os.listdir(new_path)
                            if n[0] != IGNORE_MARKER if n[0] != '.'
                            if os.path.split(n)[-1] != ASSETS_FOLDER
                            if os.path.split(n)[-1] != 'index.html'
                            if os.path.split(n)[-1] != 'index.htm'
                            if os.path.split(n)[-1] != self._short_name() + '.html'
                            if os.path.split(n)[-1] != self._short_name()[3:] + '.html'
                            if os.path.split(n)[-1] != self._short_name()[1:] + '.html'
                            ]
            else:
                bifrost.childs = []
            logging.debug('I\'m %s and my brothers are: %s' % str_tpl)
            logging.debug('My uncles are: %s' % str(bifrost.uncles))
            logging.debug('My childs are: %s' % str(bifrost.childs))
            bifrost._node_render()

    def _load_template(self):
        tmplt = self.template
        data = ''
        if tmplt is not None and os.path.exists(tmplt):
            with open (tmplt, "r") as f:
                data = f.readlines()
        return data

    def _load_content(self):
        tmplt = self.current_node
        data = ''
        if tmplt is not None and os.path.exists(tmplt):
            with open (tmplt, "r") as f:
                data = f.readlines()
        return data

    def _node_render(self, *argv):
        leaf = self
        level = leaf.current_level
        node = leaf.current_node

        file_name = os.path.split(node)[-1]
        if not leaf.is_leaf():
            # The node is a folder
            if file_name[0].isdigit and file_name[1].isdigit and file_name[2] == '_':
                # regex equivalent: ^[0-9]{2}_
                file_name = file_name[3:]
            file_name = file_name.replace(NO_LINK_MARKER, '')
            file_name = file_name.replace(ORDER_BY_DATE_MARKER, '')
            file_name += '.html'
            # The node contains a [node].html page... do not render
            if os.path.exists(os.path.join(node, file_name)):
                return

        if file_name[0].isdigit and file_name[1].isdigit and file_name[2] == '_':
            # regex equivalent: ^[0-9]{2}_
            file_name = file_name[3:]
        file_path = os.path.join(leaf.output_dir, file_name).replace(' ', '_')
        file_path = file_path.replace(NO_LINK_MARKER, '')
        file_path = file_path.replace(ORDER_BY_DATE_MARKER, '')
        file_dir = os.path.dirname(file_path)

        logging.info('Rendering [level %d page] %s' % (level, file_path))
        if not os.path.exists(file_dir):
            logging.warning('%s folder not exist. Creating...' % file_dir)
            os.makedirs(file_dir)

        content = leaf._generate()
        f = open(file_path, 'w')
        f.write(''.join(content))
        f.close()

    def _generate(self):
        out = []
        # level = self.current_level
        node = self.current_node

        render_as_html = False


        if not self.is_leaf():
            out = self._render_indexer_page()
            render_as_html = True
        else:
            # Only a file with an extension listed here is created in the static folder
            # If you want to include a certain type of file you must add to this
            # ELIF list. The renering switch is optional.
            if node[-4:].lower() == 'html' or node[-3:].lower() == 'htm':
                render_as_html = True
            elif node[-3:].lower() == 'txt':
                # TODO
                pass
            elif node[-2:].lower() == 'md':
                # TODO
                pass
            else:
                logging.warning('Node exestion not recognized, not parsing (%s)' % node)
                return out
            out = self._load_content()

        template_empty = None
        if render_as_html:
            # get the last update date of the file to be genrated
            last_update = os.path.getmtime(node)
            last_update_str = 'Last update: %s' % datetime.fromtimestamp(last_update)

            # load the template for the current directory
            template = self._load_template()
            template_empty = template.copy()
            for n, line in enumerate(template):
                # Save the current line for empty template generation.
                # The empty template is the main page tamplate with all plugins
                # executed but the built-in hook PAGE_TITLE and BODY not executed
                template_empty[n] = template[n]

                # parsing built-in hooks
                if line.find('[%PAGE_TITLE%]') >= 0:
                    template[n] = str(template[n]).replace('[%PAGE_TITLE%]', self._short_name())

                if line.find('[%BODY%]') >= 0:
                    # template[n] = out
                    template[n] = str(template[n]).replace('[%BODY%]', ''.join(flatten(out)))

                if line.find('[%LAST_UPDATE%]') >= 0:
                    template[n] = str(template[n]).replace('[%LAST_UPDATE%]', last_update_str)
                    # update also the empty template
                    template_empty[n] = template[n]

                if line.find('[%NAV_MENU%]') >= 0:
                    # update also the empty template
                    # template_empty[n] = self._gen_menu(stop_at_first=True)
                    template_empty[n] = str(template[n]).replace('[%NAV_MENU%]', ''.join(flatten(self._gen_menu(stop_at_first=True))))
                    # template[n] = self._gen_menu()
                    template[n] = str(template[n]).replace('[%NAV_MENU%]', ''.join(flatten(self._gen_menu())))

            # flatten the list
            out  = flatten(template)

        # search the hooks (i.e. plugins: [$...$])
        out = self._parse_hooks(out, template_empty)

        return out

    def _gen_menu(self, stop_at_first=False):
        menu = []

        menu_three = self._rel_path().split(os.path.sep)

        for u in self.uncles:
            if u is not None:
                sorted_uncles = self._sort_ignoring_special_chars(u)
                menu.append('<div class="deep_menu">\n')
                menu.append('<ul>\n')
                menu.append(self._list_item_from_list(sorted_uncles, menu_tree=menu_three))
                menu.append('</ul>\n')
                menu.append('</div>\n')
                if stop_at_first:
                    return menu

        sorted_brothers = self._sort_ignoring_special_chars(self.brothers)
        if sorted_brothers is not None:
            if self.parent is not None and os.path.split(self.parent)[-1].find(ORDER_BY_DATE_MARKER) != -1:
                sorted_brothers = self._sort_by_date(sorted_brothers, base_path=self.parent)

            menu.append('<div class="menu">\n')
            menu.append('<ul>\n')
            menu.append(self._list_item_from_list(sorted_brothers, menu_tree=menu_three, more_allowed=True))
            menu.append('</ul>\n')
            menu.append('</div>\n')

        sorted_childs = self._sort_ignoring_special_chars(self.childs)
        if sorted_childs is not None:
            if self.parent is not None and os.path.split(self.parent)[-1].find(ORDER_BY_DATE_MARKER) != -1:
                sorted_childs = self._sort_by_date(sorted_childs, base_path=self.parent)

            menu.append('<div class="menu">\n')
            menu.append('<ul>\n')
            menu.append(self._list_item_from_list(sorted_childs, menu_tree=menu_three, more_allowed=True))
            menu.append('</ul>\n')
            menu.append('</div>\n')

        return menu

    def _sort_ignoring_special_chars(self, list_to_sort):
        enumerate_object = enumerate([e.replace(NO_LINK_MARKER, '').replace(ORDER_BY_DATE_MARKER, '') for e in list_to_sort])
        sorted_pairs = sorted(enumerate_object, key=operator.itemgetter(1))
        sorted_indices = [index for index, element in sorted_pairs]
        return [list_to_sort[n] for n in sorted_indices]

    def _sort_by_date(self, path_list, base_path=None):
        if base_path is None:
            base_path = self.current_node
        upd_list = [os.path.getmtime(os.path.join(base_path, p)) for p in path_list]
        enumerate_object = enumerate(upd_list)
        sorted_pairs = sorted(enumerate_object, key=operator.itemgetter(1), reverse=True)
        sorted_indices = [index for index, element in sorted_pairs]
        return [path_list[n] for n in sorted_indices]

    def _render_indexer_page(self):
        page_title = self._short_name().replace(ORDER_BY_DATE_MARKER, '')
        if page_title[0].isdigit and page_title[1].isdigit and page_title[2] == '_':
            # remove the leading XX_ used for ordering menu items
            # regex equivalent: ^[0-9]{2}_
            page_title = page_title[3:]

        out = ['<h2>' + page_title.capitalize() + '</h2>\n']

        dir_list = os.listdir(self.current_node)
        dir_list = [d for d in dir_list if d[0] != '.']
        if len(dir_list) > 0:
            out.append(['<ul class="indexer_node">'])
            if self._short_name().find(ORDER_BY_DATE_MARKER) != -1:
                # Sort by date
                dir_list = self._sort_by_date(dir_list)

            for element in dir_list:
                element_path = os.path.join(self.current_node, element)
                out.append(self._list_item_from_list([element], paths=[element_path]))
                if os.path.isdir(element_path):
                    sub_dir_list = os.listdir(element_path)
                    sub_dir_list = [d for d in sub_dir_list if d[0] != '.']
                    if element + '.html' in sub_dir_list:
                        sub_dir_list.remove(element + '.html')

                    if element.find(ORDER_BY_DATE_MARKER) != -1:
                        # Order by date
                        parent_path = os.path.join(self.current_node, element)
                        sub_dir_list = self._sort_by_date(sub_dir_list, base_path=parent_path)
                    if len(sub_dir_list) > 0:
                        paths = [os.path.join(element_path,f) for f in sub_dir_list]
                        out.append(['<ul class="indexer_leaf">'])
                        out.append(self._list_item_from_list(sub_dir_list,
                                                             paths=paths))
                        out.append(['</ul>'])
            out.append(['</ul>'])
        return out

    def _list_item_from_list(self, li_list, menu_tree=None, paths=None, more_allowed=False):
        out = []
        # The standard, highlighted ("selected") and "more" menu item strings
        item_str = '<li><a href=\"{}\">{}</a></li>\n'
        item_str_selected = '<li class=\"selected\"><a href=\"{}\">{}</a></li>\n'
        item_str_more = '<li class=\"more\"><a href=\"{}\">see more ...</a></li>\n'
        # for each item in the menu, populate the <LI> tag
        for n, li in enumerate(li_list):
            if n > MAX_MENU_ENTRY-1 and self.parent is not None and more_allowed:
                parent_link = os.path.split(self.parent)[-1] + '.html'

                parent_link = parent_link.replace(ORDER_BY_DATE_MARKER, '')
                if parent_link[0].isdigit and parent_link[1].isdigit and parent_link[2] == '_':
                    # remove the leading XX_ used for ordering menu items
                    # regex equivalent: ^[0-9]{2}_
                    parent_link = parent_link[3:]
                out.append(item_str_more.format(parent_link))
                break
            if li[0] == NO_LINK_MARKER:
                # do not link files that starts with NO_LINK_MARKER marker
                continue

            # generate the item name and link to be put in <LI> item
            li_str = li.split('.')[0]
            li_str = li_str.replace(ORDER_BY_DATE_MARKER, '')
            li_link = li.replace(' ', '_')
            li_link = li_link.replace(ORDER_BY_DATE_MARKER, '')
            if len(li_link.split('.')) == 1:
                li_link += '.html'
            if len(li.split('.')) == 1:
                li_str += '/'
            if li_str[0].isdigit and li_str[1].isdigit and li_str[2] == '_':
                # remove the leading XX_ used for ordering menu items
                # regex equivalent: ^[0-9]{2}_
                li_str = li_str[3:]
                li_link = li_link[3:]

            li_str = li_str.replace('_', ' ')
            if li_str[-1] != '/' and paths is not None:
                # If the menu entry is not a folder ...
                size_str = os.stat(paths[n]).st_size
                upd_str = datetime.fromtimestamp(os.path.getmtime(paths[n]))
                li_str = '<span class="leaf_link">%s</span>' % (li_str.capitalize())
                # li_str = '<span class="num_ord">0x%.4x</span> - ' % n + li_str
                li_str += ' - <span class="update_str_list">last update: %s</span>' % upd_str
                li_str += ' - <span class="file_size">(%s bytes)</span>' % size_str
            if menu_tree is not None and li in menu_tree:
                # if the menu entry is the current selected level, use the
                # "selected" CSS class for highlighting the entry
                out.append(item_str_selected.format(li_link, li_str))
            else:
                # not a "selected" item
                out.append(item_str.format(li_link, li_str))
        return out

    def _parse_hooks(self, lines, template_empty):
        if template_empty is not None:
            template_empty = self._parse_hooks(flatten(template_empty), None)

        context = DrasilContext()
        context.plugins = self.plugins
        context.src_root = self.src_root
        context.output_dir = self.output_dir
        context.current_node = self.current_node
        context.current_level = self.current_level
        context.brothers = self.brothers
        context.uncles = self.uncles
        context.childs = self.childs
        context.template = self.template

        for n, l in enumerate(lines):
            stop = False
            while not stop:
                if l.find(LEFT_HOOK_MARKER) >= 0 and l.find(RIGHT_HOOK_MARKER) >= 0:
                    # I've found a hook... parse it
                    l = self._apply_hooks(l, context, template_empty)
                else:
                    stop = True
            lines[n] = l
        return lines

    def _apply_hooks(self, text, context, template_empty):
        # logging.debug('Hook found: %s' % text)
        hook_begin = text.find(LEFT_HOOK_MARKER) + 2
        hook_end = text.find(RIGHT_HOOK_MARKER)
        plug_run = self.plugins.run_hooks(text[hook_begin:hook_end], context, template_empty)
        logging.debug('Hook found: %s' % text[hook_begin:hook_end])
        if plug_run is None:
            plug_run =  '[HOOK NOT FOUND: ' + text[hook_begin:hook_end] + ']'
        text =  text[:hook_begin - 2] + str(plug_run) + text[hook_end+2:]
        return text

    def is_leaf(self):
        return os.path.isfile(self.current_node)

    def _rel_path(self):
        return self.current_node.replace(self.src_root, '')

    def _short_name(self):
        name = os.path.split(self.current_node)[-1].split('.')[0]
        name = name.replace(ORDER_BY_DATE_MARKER, '')
        if len(name) > 3:
            if name[0].isdigit and name[1].isdigit and name[2] == '_':
                # regex equivalent: ^[0-9]{2}_
                name = name[3:]
        return name

# AUX methods


def flatten(a):
    # flatten a list of strings
    rt = []
    for i in a:
        if isinstance(i, list):
            rt.extend(flatten(i))
        else:
            rt.append(i)
    return rt
