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
    template_empty = None
    out_dir = None

    def pre(self, *argv):
        pass

    def run(self, *argv):
        caller = path.split(argv[1].current_node)[-1]
        DrasilPlug.out_dir = argv[1].output_dir

        tag_list = argv[0]
        DrasilPlug.template_empty = argv[2]
        # DrasilPlug.tag_struct.append({'caller': caller, 'tags': tag_list})
        tag_str = '<span class=\"tag_link\"><a href=\"tag_{}.html\">{}</a></span>'
        ret_str = ''
        for t in tag_list:
            ret_str += tag_str.format(t, t.upper())
            if t in DrasilPlug.tag_struct:
                if caller not in DrasilPlug.tag_struct[t]:
                    DrasilPlug.tag_struct[t].append(caller)
            else:
                DrasilPlug.tag_struct[t] = [caller]
        return '<div class=\"tag_list\">%s</div>' % ret_str

    def post(self, *argv):

        for t in DrasilPlug.tag_struct:
            content = self._render_tag_page(t, DrasilPlug.tag_struct[t])
            link = t.replace(' ', '_')
            file_path = path.join(DrasilPlug.out_dir, 'tag_%s.html' % link)
            f = open(file_path, 'w')
            f.write(''.join(content))
            f.close()

    def _render_tag_page(self, tag, page_list):
        template = DrasilPlug.template_empty.copy()

        for n, line in enumerate(template):
            if isinstance(line, list):
                line = ''.join(flatten(line))

            if line.find('[%PAGE_TITLE%]') >= 0:
                template[n] = str(template[n]).replace('[%PAGE_TITLE%]', 'tag: %s' % tag.replace('_', ' '))

            if line.strip() == '[%BODY%]':
                template[n] = '<h2 class=\"tagged\">%s</h2>\n' % tag.upper()
                template[n] += '<ul class=\"tagged\">\n'
                for p in page_list:
                    if p[0].isdigit and p[1].isdigit and p[2] == '_':
                        # remove the leading XX_ used for ordering
                        p = p[3:]
                    sp = p.split('.')[0].replace('_', ' ').capitalize()
                    link = p.replace(' ', '_')
                    template[n] += '<li><a href=\"%s\">%s</a></li>\n' % (p, sp)
                template[n] += '</ul>\n'

                tag_str = '<span class=\"tag_link\"><a href=\"tag_{}.html\">{}</a></span>'
                all_tags_str = ' '.join([tag_str.format(t, t.upper()) for t in DrasilPlug.tag_struct])
                all_tags_str = '<div class=\"all_tags\">' + all_tags_str + '</div>\n'
                template[n] += all_tags_str

        return flatten(template)

def flatten(a):
    # flatten a list of strings
    rt = []
    for i in a:
        if isinstance(i, list):
            rt.extend(flatten(i))
        else:
            rt.append(i)
    return rt