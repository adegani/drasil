import os.path as path
from ..drasil_context import DrasilContext


class DrasilPlug():
    """Collect page tags and generate a listing page for each tag."""
    hooks = ['tag']
    name = 'Tag'
    description = 'Implement a simple tagging feature'
    help_str = 'You can tag a page using [$tag:tag_one:tag_two$] so that page '
    help_str += 'will be present in the tag specific page. For each tag, '
    help_str += 'a page called tag_tagname.html will be created. The page will'
    help_str += ' list each page that calls that given tag'

    pages_by_tag = {}
    template_empty = None
    output_dir = None

    def pre(self, *argv):
        """Perform no pre-build work.

        Args:
            *argv: Lifecycle arguments supplied by the plugin dispatcher.
        """
        pass

    def run(self, *argv):
        """Register tags for the current page and return tag-link markup.

        Args:
            *argv: Hook arguments, rendering context, and empty template.

        Returns:
            HTML fragment containing links for the registered tags.
        """
        page_name = path.split(argv[1].current_node)[-1]
        DrasilPlug.output_dir = argv[1].output_dir

        tag_list = argv[0]
        DrasilPlug.template_empty = argv[2]
        tag_str = '<span class=\"tag_link\"><a href=\"tag_{}.html\">{}</a></span>'
        tag_links_html = ''
        for tag in tag_list:
            tag_links_html += tag_str.format(tag, tag.upper())
            if tag in DrasilPlug.pages_by_tag:
                if page_name not in DrasilPlug.pages_by_tag[tag]:
                    DrasilPlug.pages_by_tag[tag].append(page_name)
            else:
                DrasilPlug.pages_by_tag[tag] = [page_name]
        return '<div class=\"tag_list\">%s</div>' % tag_links_html

    def post(self, *argv):
        """Write generated listing pages for every collected tag.

        Args:
            *argv: Lifecycle arguments supplied by the plugin dispatcher.
        """

        for tag, page_names in DrasilPlug.pages_by_tag.items():
            content = self._render_tag_page(tag, page_names)
            link = tag.replace(' ', '_')
            file_path = path.join(DrasilPlug.output_dir, 'tag_%s.html' % link)
            with open(file_path, 'w') as file:
                file.write(''.join(content))

    def _render_tag_page(self, tag, page_list):
        """Render the tag page body within the captured empty template.

        Args:
            tag: Tag whose page is being generated.
            page_list: Source page names registered for the tag.

        Returns:
            Flattened HTML lines for the tag page.
        """
        template = DrasilPlug.template_empty.copy()

        for index, line in enumerate(template):
            if isinstance(line, list):
                line = ''.join(flatten(line))

            if line.find('[%PAGE_TITLE%]') >= 0:
                template[index] = str(template[index]).replace('[%PAGE_TITLE%]', 'tag: %s' % tag.replace('_', ' '))

            if line.strip() == '[%BODY%]':
                template[index] = '<h2 class=\"tagged\">%s</h2>\n' % tag.upper()
                template[index] += '<ul class=\"tagged\">\n'
                for page_name in page_list:
                    if page_name[0] == '$':
                        continue
                    if len(page_name) >= 3 and page_name[:2].isdigit() and page_name[2] == '_':
                        # remove the leading number XX_ used for ordering
                        page_name = page_name[3:]
                    page_title = page_name.split('.')[0].replace('_', ' ').capitalize()
                    link = page_name.replace(' ', '_')
                    template[index] += '<li><a href=\"%s\">%s</a></li>\n' % (link, page_title)
                template[index] += '</ul>\n'

                tag_str = '<span class=\"tag_link\"><a href=\"tag_{}.html\">{}</a></span>'
                all_tags_str = ' '.join([tag_str.format(tag_name, tag_name.upper()) for tag_name in DrasilPlug.pages_by_tag])
                all_tags_str = '<div class=\"all_tags\">' + all_tags_str + '</div>\n'
                template[index] += all_tags_str

        return flatten(template)


def flatten(items):
    """Recursively flatten nested lists while preserving item order.

    Args:
        items: List that may recursively contain other lists.

    Returns:
        Flat list containing all non-list items in traversal order.
    """
    flattened_items = []
    for item in items:
        if isinstance(item, list):
            flattened_items.extend(flatten(item))
        else:
            flattened_items.append(item)
    return flattened_items
