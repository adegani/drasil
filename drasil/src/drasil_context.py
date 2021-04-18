import copy
import logging
import os.path
from .drasil_plugins import DrasilPlugin

class DrasilContext(object):
    def __init__(self):
        super(DrasilContext, self).__init__()
        DrasilContext.tot_steps = 0

        self.src_root = None
        self.output_dir = None
        self.current_node = None
        self.current_level = 0

        self.brothers = None
        self.prev_menu_elements = []
    
        self.template = None

        self.plugins = DrasilPlugin()

    def generate(self):
        out = ''
        if not self.is_leaf():
            out = '<h1>GEN: %s<h1>' % self.rel_path()
        else:
            out = '<h1>NOTGEN: %s<h1>' % self.rel_path()
        return out

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

            str_tpl = (step.rel_path(), ', '.join(step.brothers))
            logging.debug('I\'m %s and my brothers are: %s' % str_tpl)
            step.node_render()

    def node_render(self, *argv):
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
        else:
            if node[-4:] != 'html':
                logging.warning('The node exestions is not .html, not parsing (%s)' % node)
                return

        file_path = os.path.join(leaf.output_dir, file_name).replace(' ', '_')
        file_dir = os.path.dirname(file_path)

        logging.info('Rendering [level %d page] %s' % (level, file_path))
        if not os.path.exists(file_dir):
            logging.warning('%s folder not exist. Creating...' % file_dir)
            os.makedirs(file_dir)

        f = open(file_path, 'w')
        f.write(leaf.generate())
        f.close()

    def is_leaf(self):
        return os.path.isfile(self.current_node)

    def rel_path(self):
        return self.current_node.replace(self.src_root, '')
