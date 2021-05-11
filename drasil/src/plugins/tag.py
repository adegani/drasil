import os.path as path
from ..drasil_context import DrasilContext

class DrasilPlug():
    hooks = ['tag']
    name = 'Tag' 
    description = 'Implement a simple tagging feature'
    help_str = 'You can tag a page using [$tag:tag_one:tag_two$] so that page '
    help_str += 'will be present in the tag specific page. For each tag, '
    help_str += 'a page called tag_tagname.html will be created. The page will '
    help_str += 'list each page that calls that given tag'

    tag_struct = {}
    
    def pre(self, *argv):
        pass

    def run(self, *argv):
        print('TAG CALLED:')
        caller = path.split(argv[1].current_node)[-1]
        tag_list = argv[0] 

        # DrasilPlug.tag_struct.append({'caller': caller, 'tags': tag_list})
        tag_str = '<span class=\"tag_link\"><a href=\"tag_{}.html\">{}</a></span>'
        ret_str = ''
        for t in tag_list:
            ret_str += tag_str.format(t, t.replace('_', ' '))
            if t in DrasilPlug.tag_struct:
                DrasilPlug.tag_struct[t].append(caller)
            else:
                DrasilPlug.tag_struct[t] = [caller]
        return ret_str

    def post(self, *argv):
        print('POST')
        print(DrasilPlug.tag_struct)
        pass