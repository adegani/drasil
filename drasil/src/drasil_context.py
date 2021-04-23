import copy
import logging
import os.path
from .drasil_plugins import DrasilPlugin

class DrasilContext(object):
    def __init__(self, plugins=None):
        super(DrasilContext, self).__init__()
        DrasilContext.tot_steps = 0

        self.plugins = plugins
        self.src_root = None
        self.output_dir = None
        self.current_node = None
        self.current_level = 0

        self.brothers = None
        self.prev_menu_elements = []
    
        self.template = None

    def walk(self):
        bifrost = self
        DrasilContext.tot_steps += 1
        root = bifrost.current_node
        level = bifrost.current_level

        step = copy.copy(bifrost)
        step.current_level += 1

        step.brothers = [n for n in os.listdir(root) if n[0] is not '_']

        if level == 0:
            print('+')
        print('='*(level+1))

        for node in os.listdir(root):
            # print('NODE: %s' % node)
            if node[0] == '_':
                continue

            new_path = os.path.join(root, node)
            step.current_node = new_path
            if os.path.isfile(new_path):
                print('|'*(level+1))
            if os.path.isdir(new_path):
                step.walk()

            str_tpl = (step._rel_path(), ', '.join(step.brothers))
            logging.debug('I\'m %s and my brothers are: %s' % str_tpl)
            step._node_render()

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
            file_name += '.html'
            # The node contains a [node].html page... do not render
            if os.path.exists(os.path.join(node, file_name)):
                return

        file_path = os.path.join(leaf.output_dir, file_name).replace(' ', '_')
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
        out = ''
        level = self.current_level
        node = self.current_node

        render_as_html = False

        if not self.is_leaf():
            out = '<h1>GEN: %s<h1>' % self._rel_path()
        else:
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
                return
            out = self._load_content()
        
        if render_as_html:
            template = self._load_template()
            for n, line in enumerate(template):
                # parsing built-in hooks
                template[n] = str(template[n]).replace('[$PAGE_TITLE$]', self._short_name())
                template[n] = str(template[n]).replace('[$NAV_MENU$]', 'menu') # TODO
                if line.strip() == '[$BODY$]':
                    template[n] = out

            # flatten the list
            out  = flatten(template)

        # search the hooks (i.e. plugins: [$...$])
        out = self._parse_hooks(out)

        return out

    def _parse_hooks(self, lines):
        for n, l in enumerate(lines):
            if l.find('[$') >= 0 and l.find('$]') >= 0:
                # I've found a hook... parse it
                lines[n] = self._apply_hooks(l)
        return lines

    def _apply_hooks(self, text):
        hook_begin = text.find('[$') + 2
        hook_end = text.find('$]')
        plug_run = self.plugins.run_hooks(text[hook_begin:hook_end])
        text =  text[:hook_begin - 2] + str(plug_run) + text[hook_end+2:]
        return text

    def is_leaf(self):
        return os.path.isfile(self.current_node)

    def _rel_path(self):
        return self.current_node.replace(self.src_root, '')

    def _short_name(self):
        return os.path.split(self.current_node)[-1].split('.')[0]
# AUX methods

def flatten(A):
    # flatten a list of strings
    rt = []
    for i in A:
        if isinstance(i,list):
            rt.extend(flatten(i))
        else:
            rt.append(i)
    return rt