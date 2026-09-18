from html import escape
import logging
import os.path
from datetime import datetime
from urllib.parse import quote

from .drasil_context import DrasilContext

ASSETS_FOLDER = 'assets'

IGNORE_MARKER = '_'
NO_LINK_MARKER = '$'
ORDER_BY_DATE_MARKER = '%'
LEFT_HOOK_MARKER = '[$'
RIGHT_HOOK_MARKER = '$]'


class DrasilBifrost:
    """Traverse a source tree and render its files and directory indexes."""

    def __init__(self, version, plugins=None):
        """Initialise renderer state for the supplied version and plugins.

        Args:
            version: Drasil version string exposed to templates.
            plugins: Plugin dispatcher used to expand plugin hooks.
        """
        self.version = version

        DrasilBifrost.tot_steps = 0

        self.plugins = plugins
        self.src_root = None
        self.output_dir = None
        self.current_node = None
        self.current_level = 0

        self.parent = None
        self.siblings = []
        self.ancestor_siblings = []
        self.children = []

        self.template = None
        self.template_file = None
        self.template_is_parsed = False

    def walk(self):
        """Render the source tree without copying renderer/plugin state."""
        self._walk(self.current_node, self.current_level, self.parent, self.ancestor_siblings)

    def _walk(self, root, level, parent_directory, ancestor_siblings):
        """Recursively render entries below ``root`` with navigation state.

        Args:
            root: Directory currently being traversed.
            level: Depth of ``root`` in the source tree.
            parent_directory: Parent directory used for sibling navigation.
            ancestor_siblings: Navigation entry lists belonging to ancestor directories.
        """
        DrasilBifrost.tot_steps += 1
        siblings = self._navigable_children(root)

        if level == 0:
            print('+')
        print('='*(level+1), end='-\n')

        for node in os.listdir(root):
            if self._is_ignored(node):
                print('|', end='')
                continue

            new_path = os.path.join(root, node)
            if os.path.isfile(new_path):
                print('^', end='')
            elif os.path.isdir(new_path):
                print('/'*(level+1))
                print('+', end='')
                self._walk(new_path, level + 1, root, [*ancestor_siblings, siblings])

            children = self._navigable_children(new_path) if os.path.isdir(new_path) else []
            self.current_node = new_path
            self.current_level = level + 1
            self.parent = parent_directory
            self.siblings = siblings
            self.ancestor_siblings = ancestor_siblings
            self.children = children

            logging.debug("I'm %s and my siblings are: %s", self._rel_path(), ', '.join(siblings))
            logging.debug('My ancestor siblings are: %s', ancestor_siblings)
            logging.debug('My children are: %s', children)
            self._node_render()

    def _is_ignored(self, name):
        """Return whether an entry is excluded from traversal and menus.

        Args:
            name: Basename of the candidate filesystem entry.

        Returns:
            True when the entry is hidden, marked ignored, or is ``assets``.
        """
        return name.startswith((IGNORE_MARKER, '.')) or name == ASSETS_FOLDER

    def _navigable_children(self, directory):
        """Return entries suitable for menus, excluding generated pages.

        Args:
            directory: Directory whose entries are inspected.

        Returns:
            Entry names that may appear in navigation menus.
        """
        directory_name = os.path.splitext(os.path.basename(directory))[0]
        directory_name = self._strip_order_prefix(directory_name)
        generated_names = {
            'index.html', 'index.htm', f'{directory_name}.html',
            f'{directory_name[3:]}.html', f'{directory_name[1:]}.html',
        }
        return [
            name for name in os.listdir(directory)
            if not self._is_ignored(name) and name not in generated_names
        ]

    @staticmethod
    def _strip_order_prefix(name):
        """Remove a leading ``NN_`` ordering prefix, if present.

        Args:
            name: File or directory name to normalise.

        Returns:
            ``name`` without its ordering prefix, when one exists.
        """
        return name[3:] if len(name) >= 3 and name[:2].isdigit() and name[2] == '_' else name

    def _load_template(self):
        """Load and cache the base template, or an empty fallback template.

        Returns:
            Template lines after context-independent substitutions.
        """
        if not self.template_is_parsed:
            template_path = self.template_file
            data = ['']
            if template_path is not None and os.path.exists(template_path):
                with open(template_path, encoding='utf-8') as file:
                    data = file.readlines()
            self.template = data
            self._parse_template()
            self.template_is_parsed = True
        return self.template

    def _parse_template(self):
        """Apply context-independent substitutions to the cached template."""
        for index, line in enumerate(self.template):
            if line.find('[%VER%]') >= 0:
                self.template[index] = str(self.template[index]).replace('[%VER%]', self.version)

    def _load_content(self, binary=False):
        """Read the current node as text lines or binary chunks.

        Args:
            binary: Read bytes instead of UTF-8 text when true.

        Returns:
            Lines from the current node, or an empty string when unavailable.
        """
        content_path = self.current_node
        mode = 'r'
        if binary:
            mode += 'b'
        data = ''
        if content_path is not None and os.path.exists(content_path):
            open_kwargs = {} if binary else {'encoding': 'utf-8'}
            with open(content_path, mode, **open_kwargs) as file:
                data = file.readlines()
        return data

    def _node_render(self):
        """Render the current file or directory index to the output folder.
        """
        leaf = self
        level = leaf.current_level
        node = leaf.current_node

        file_name = os.path.split(node)[-1]
        if not leaf.is_leaf():
            # The node is a folder
            if self._has_order_prefix(file_name):
                # regex equivalent: ^[0-9]{2}_
                file_name = file_name[3:]
            file_name = file_name.replace(NO_LINK_MARKER, '')
            file_name = file_name.replace(ORDER_BY_DATE_MARKER, '')
            file_name += '.html'
            # The node contains a [node].html page... do not render
            if os.path.exists(os.path.join(node, file_name)):
                return

        if self._has_order_prefix(file_name):
            # regex equivalent: ^[0-9]{2}_
            file_name = file_name[3:]
        file_path = os.path.join(leaf.output_dir, file_name).replace(' ', '_')
        file_path = file_path.replace(NO_LINK_MARKER, '')
        file_path = file_path.replace(ORDER_BY_DATE_MARKER, '')
        file_dir = os.path.dirname(file_path)

        logging.info('Rendering [level %d page] %s', level, file_path)
        if not os.path.exists(file_dir):
            logging.warning('%s folder not exist. Creating...', file_dir)
            os.makedirs(file_dir, exist_ok=True)

        content = leaf._generate()

        if self.is_leaf() and os.path.splitext(node)[1].lower() == '.pdf':
            with open(file_path, 'wb') as file:
                file.writelines(content)
        else:
            with open(file_path, 'w', encoding='utf-8') as file:
                file.write(''.join(content))

    def _generate(self):
        """Generate rendered content for the current node.

        Returns:
            Rendered text lines or binary chunks for PDF files.
        """
        rendered = []
        # level = self.current_level
        node = self.current_node

        render_as_html = False
        copy_and_link = False

        if not self.is_leaf():
            rendered = self._render_indexer_page()
            render_as_html = True
        else:
            # Only a file with an extension listed here is created in the static folder
            # If you want to include a certain type of file you must add to this
            # ELIF list. The renering switch is optional.
            suffix = os.path.splitext(node)[1].lower()
            if suffix in {'.html', '.htm'}:
                render_as_html = True
            elif suffix == '.pdf':
                copy_and_link = True
            elif suffix == '.txt':
                # TODO
                pass
            elif suffix == '.md':
                # TODO
                pass
            else:
                logging.warning('Node exestion not recognized, not parsing (%s)' % node)
                # return rendered

            rendered = self._load_content(binary=copy_and_link)

        if not copy_and_link:
            template_empty = None

            # load the template for the current directory
            # Plugin hooks depend on the current node, so do not cache their output.
            template = self._parse_plugins_hooks(self._load_template().copy(), None)
            template_empty = template.copy()
            if render_as_html:
                # run only template built-in hooks
                rendered = self._parse_only_template_hooks(node, rendered, template, template_empty)

            # run built-in hooks
            rendered = self._parse_builtin_hooks(node, rendered)
            # run plug-ins hooks (i.e. plugins: [$...$])
            rendered = self._parse_plugins_hooks(rendered, template_empty)

        return rendered

    @staticmethod
    def _has_order_prefix(name):
        """Return whether ``name`` starts with the ``NN_`` ordering convention.

        Args:
            name: File or directory name to inspect.

        Returns:
            True when ``name`` begins with two digits followed by an underscore.
        """
        return len(name) >= 3 and name[:2].isdigit() and name[2] == '_'

    def _parse_builtin_hooks(self, node, rendered_lines):
        """Expand built-in placeholders in rendered content.

        Args:
            node: Source node currently rendered.
            rendered_lines: Nested or flat rendered content lines.

        Returns:
            Flattened content with built-in hooks expanded.
        """
        ver_str = self.version

        for index, line in enumerate(rendered_lines):
            # parsing built-in hooks
            if line.find('[%VER%]') >= 0:
                rendered_lines[index] = str(rendered_lines[index]).replace('[%VER%]', ver_str)

            if line.find('[%TREE_GEN%]') >= 0:
                rendered_lines[index] = str(rendered_lines[index]).replace('[%TREE_GEN%]', tree_generator(self.src_root))

        # flatten the list
        return flatten(rendered_lines)

    def _parse_only_template_hooks(self, node, rendered_lines, template, template_empty):
        """Fill page-specific template placeholders and retain an empty template.

        Args:
            node: Source node currently rendered.
            rendered_lines: Rendered source content inserted into the template body.
            template: Template lines to populate.
            template_empty: Template copy retained for post-build plugins.

        Returns:
            Flattened populated template lines.
        """
        # get the last update date of the file to be genrated
        last_update = os.path.getmtime(node)
        last_update_str = '%s' % datetime.fromtimestamp(last_update)
        for index, line in enumerate(template):
            # Save the current line for empty template generation.
            # The empty template is the main page tamplate with all plugins
            # executed but the built-in hook PAGE_TITLE and BODY not executed
            template_empty[index] = template[index]

            # parsing built-in hooks
            if line.find('[%PAGE_TITLE%]') >= 0:
                template[index] = str(template[index]).replace('[%PAGE_TITLE%]', self._short_name())

            if line.find('[%BODY%]') >= 0:
                template[index] = str(template[index]).replace('[%BODY%]', ''.join(flatten(rendered_lines)))

            if line.find('[%LAST_UPDATE%]') >= 0:
                template[index] = str(template[index]).replace('[%LAST_UPDATE%]', last_update_str)
                # update also the empty template
                template_empty[index] = template[index]

            if line.find('[%NAV_MENU%]') >= 0:
                template_empty[index] = str(template[index]).replace('[%NAV_MENU%]', ''.join(flatten(self._gen_menu(stop_at_first=True))))
                template[index] = str(template[index]).replace('[%NAV_MENU%]', ''.join(flatten(self._gen_menu())))

        # flatten the list
        return flatten(template)

    def _gen_menu(self, stop_at_first=False):
        """Build HTML navigation menus for ancestor, sibling, and child entries.

        Args:
            stop_at_first: Stop after the nearest ancestor menu when true.

        Returns:
            Nested HTML fragments that compose the navigation menu.
        """
        menu = []

        selected_path_parts = self._rel_path().split(os.path.sep)

        for ancestor_entries in self.ancestor_siblings:
            if ancestor_entries is not None:
                sorted_ancestor_entries = self._sort_ignoring_special_chars(ancestor_entries)
                menu.append('<div class="deep_menu">\n')
                menu.append('<ul>\n')
                menu.append(self._list_item_from_list(sorted_ancestor_entries, selected_path_parts=selected_path_parts))
                menu.append('</ul>\n')
                menu.append('</div>\n')
                if stop_at_first:
                    return menu

        sorted_siblings = self._sort_ignoring_special_chars(self.siblings)
        if self.parent is not None and ORDER_BY_DATE_MARKER in os.path.basename(self.parent):
            sorted_siblings = self._sort_by_date(sorted_siblings, base_path=self.parent)

        if sorted_siblings:
            menu.append('<div class="menu">\n')
            menu.append('<ul>\n')
            menu.append(self._list_item_from_list(sorted_siblings, selected_path_parts=selected_path_parts))
            menu.append('</ul>\n')
            menu.append('</div>\n')

        sorted_children = self._sort_ignoring_special_chars(self.children)
        if self.is_leaf() is False and ORDER_BY_DATE_MARKER in os.path.basename(self.current_node):
            sorted_children = self._sort_by_date(sorted_children, base_path=self.current_node)

        if sorted_children:
            menu.append('<div class="menu">\n')
            menu.append('<ul>\n')
            menu.append(self._list_item_from_list(sorted_children, selected_path_parts=selected_path_parts))
            menu.append('</ul>\n')
            menu.append('</div>\n')

        return menu

    def _sort_ignoring_special_chars(self, list_to_sort):
        """Sort entries alphabetically without navigation marker characters.

        Args:
            list_to_sort: Entry names to sort.

        Returns:
            A new list ordered case-insensitively after marker removal.
        """
        return sorted(
            list_to_sort,
            key=lambda name: name.replace(NO_LINK_MARKER, '').replace(ORDER_BY_DATE_MARKER, '').casefold(),
        )

    def _sort_by_date(self, path_list, base_path=None):
        """Sort entries by modification time, newest first.

        Args:
            path_list: Entry names relative to ``base_path``.
            base_path: Directory containing the entries; defaults to current node.

        Returns:
            A new list ordered from newest to oldest modification time.
        """
        if base_path is None:
            base_path = self.current_node
        return sorted(
            path_list,
            key=lambda path: os.path.getmtime(os.path.join(base_path, path)),
            reverse=True,
        )

    def _render_indexer_page(self):
        """Create the HTML body for a generated directory index page.

        Returns:
            Nested HTML fragments representing the current directory contents.
        """
        page_title = self._short_name().replace(ORDER_BY_DATE_MARKER, '')
        if self._has_order_prefix(page_title):
            # remove the leading XX_ used for ordering menu items
            # regex equivalent: ^[0-9]{2}_
            page_title = page_title[3:]

        html_fragments = ['<h2>' + escape(page_title.capitalize()) + '</h2>\n']

        dir_list = sorted(name for name in os.listdir(self.current_node) if not self._is_ignored(name))
        if dir_list:
            html_fragments.append(['<ul class="indexer_node">'])
            if self._short_name().find(ORDER_BY_DATE_MARKER) != -1:
                # Sort by date
                dir_list = self._sort_by_date(dir_list)

            singleton_count = 0
            already_printed_root = False
            for index, element in enumerate(dir_list):
                element_path = os.path.join(self.current_node, element)
                if os.path.isdir(element_path):
                    html_fragments.append(self._list_item_from_list([element], entry_paths=[element_path], index_offset=index))
                    sub_dir_list = [name for name in os.listdir(element_path) if not self._is_ignored(name)]
                    if element + '.html' in sub_dir_list:
                        sub_dir_list.remove(element + '.html')

                    if element.find(ORDER_BY_DATE_MARKER) != -1:
                        # Order by date
                        parent_path = os.path.join(self.current_node, element)
                        sub_dir_list = self._sort_by_date(sub_dir_list, base_path=parent_path)
                    if len(sub_dir_list) > 0:
                        entry_paths = [os.path.join(element_path, entry_name) for entry_name in sub_dir_list]
                        html_fragments.append(['<ul class="indexer_leaf">'])
                        html_fragments.append(self._list_item_from_list(sub_dir_list,
                                                                        entry_paths=entry_paths))
                        html_fragments.append(['</ul>'])
                else:
                    if not already_printed_root:
                        html_fragments.append('<li><a href="#"></a></li>')
                        already_printed_root = True
                    html_fragments.append(['<ul class="indexer_leaf">'])
                    html_fragments.append(self._list_item_from_list([element], entry_paths=[element_path], index_offset=singleton_count))
                    html_fragments.append(['</ul>'])
                    singleton_count += 1


            html_fragments.append(['</ul>'])
        return html_fragments

    def _list_item_from_list(self, entry_names, index_offset=0, selected_path_parts=None, entry_paths=None):
        """Render entries as safe HTML list items, optionally with metadata.

        Args:
            entry_names: Entry names to convert into list items.
            index_offset: Offset used for hexadecimal item numbering.
            selected_path_parts: Relative path components selected in navigation.
            entry_paths: Filesystem paths used to display file metadata.

        Returns:
            HTML ``<li>`` fragments for every linkable entry.
        """
        html_items = []
        # The standard and highlighted ("selected")
        item_str = '<li><a href=\"{}\">{}</a></li>\n'
        item_str_selected = '<li class=\"selected\"><a href=\"{}\">{}</a></li>\n'
        # for each item in the menu, populate the <LI> tag
        for index, entry_name in enumerate(entry_names):
            if entry_name[0] == NO_LINK_MARKER:
                # do not link files that starts with NO_LINK_MARKER marker
                continue

            # generate the item name and link to be put in <LI> item
            display_name, extension = os.path.splitext(entry_name)
            extension = extension[1:]
            display_name = display_name.replace(ORDER_BY_DATE_MARKER, '')
            link_target = entry_name.replace(' ', '_')
            link_target = link_target.replace(ORDER_BY_DATE_MARKER, '')
            if not extension:
                link_target += '.html'
            if not extension:
                display_name += '/'
            if self._has_order_prefix(display_name):
                # remove the leading XX_ used for ordering menu items
                # regex equivalent: ^[0-9]{2}_
                display_name = display_name[3:]
                link_target = link_target[3:]

            display_name = display_name.replace('_', ' ')
            if display_name[-1] != '/' and entry_paths is not None:
                # If the menu entry is not a folder ...
                size_str = os.stat(entry_paths[index]).st_size
                upd_str = datetime.fromtimestamp(os.path.getmtime(entry_paths[index]))
                hex_string = '<span class="hex_num">0x%02x</span>' % (index + index_offset)
                display_name = '<span class="leaf_link">%s %s.%s</span>' % (hex_string, escape(display_name.capitalize()), escape(extension))
                display_name += ' - <span class="update_str_list">last update: %s</span>' % upd_str
                display_name += ' - <span class="file_size">(%s bytes)</span>' % size_str
            safe_link = escape(quote(link_target, safe='/._-'), quote=True)
            if entry_paths is None:
                display_name = escape(display_name)
            if selected_path_parts is not None and entry_name in selected_path_parts:
                # if the menu entry is the current selected level, use the
                # "selected" CSS class for highlighting the entry
                html_items.append(item_str_selected.format(safe_link, display_name))
            else:
                # not a "selected" item
                html_items.append(item_str.format(safe_link, display_name))
        return html_items

    def _parse_plugins_hooks(self, lines, template_empty):
        """Expand plugin hook markers in lines using the current render context.

        Args:
            lines: Lines potentially containing plugin hook markers.
            template_empty: Empty template provided to plugins that need it.

        Returns:
            Input lines with plugin markers expanded in place.
        """
        if template_empty is not None:
            template_empty = self._parse_plugins_hooks(flatten(template_empty), None)

        context = DrasilContext()
        context.plugins = self.plugins
        context.src_root = self.src_root
        context.output_dir = self.output_dir
        context.current_node = self.current_node
        context.current_level = self.current_level
        context.siblings = self.siblings
        context.ancestor_siblings = self.ancestor_siblings
        context.children = self.children
        context.template = self.template_file

        for index, line in enumerate(lines):
            for _ in range(100):
                if LEFT_HOOK_MARKER not in line or RIGHT_HOOK_MARKER not in line:
                    break
                updated_line = self._apply_hooks(line, context, template_empty)
                if updated_line == line:
                    logging.warning('Hook expansion made no progress: %s', line)
                    break
                line = updated_line
            else:
                logging.warning('Stopped hook expansion after 100 replacements: %s', line)
            lines[index] = line
        return lines

    def _apply_hooks(self, text, context, template_empty):
        """Replace the first plugin hook marker found in ``text``.

        Args:
            text: Text containing at least one plugin hook marker.
            context: Rendering context passed to the plugin.
            template_empty: Empty template supplied to the plugin.

        Returns:
            Text with its first plugin marker replaced.
        """
        # logging.debug('Hook found: %s' % text)
        hook_begin = text.find(LEFT_HOOK_MARKER) + 2
        hook_end = text.find(RIGHT_HOOK_MARKER)
        plug_run = self.plugins.run_hooks(text[hook_begin:hook_end], context, template_empty)
        logging.debug('Hook found: %s' % text[hook_begin:hook_end])
        if plug_run is None:
            plug_run = '[HOOK NOT FOUND: ' + text[hook_begin:hook_end] + ']'
        text = text[:hook_begin - 2] + str(plug_run) + text[hook_end+2:]
        return text

    def is_leaf(self):
        """Return whether the current node is a file.

        Returns:
            True when the current node exists and is a regular file.
        """
        return os.path.isfile(self.current_node)

    def _rel_path(self):
        """Return the current node path relative to the source root.

        Returns:
            Filesystem path from source root to current node.
        """
        return os.path.relpath(self.current_node, self.src_root)

    def _short_name(self):
        """Return the display name of the current node without ordering markers.

        Returns:
            Current node basename without extension and special ordering markers.
        """
        name = os.path.split(self.current_node)[-1].split('.')[0]
        name = name.replace(ORDER_BY_DATE_MARKER, '')
        return self._strip_order_prefix(name)


# AUX methods
def is_integer(string):
    """Return whether ``string`` can be converted to an integer.

    Args:
        string: Value to attempt to convert to an integer.

    Returns:
        True when the conversion succeeds, otherwise false.
    """
    try:
        int(string)
    except (TypeError, ValueError):
        return False
    return True

def tree_generator(root, level: int=-1, limit_to_directories: bool=False,
         length_limit: int=1000):
    """Return a bounded HTML rendering of the directory tree below ``root``.

    Args:
        root: Root directory of the tree.
        level: Maximum depth to render; a negative value is unlimited.
        limit_to_directories: Exclude files when true.
        length_limit: Maximum number of tree lines to include.

    Returns:
        HTML fragment containing the directory tree and item counts.
    """
    from pathlib import Path
    from itertools import islice

    anchor_str = '<a href="{}">{}</a>'

    space =  '&nbsp;&nbsp;&nbsp;&nbsp;'
    branch = '│&nbsp;&nbsp;&nbsp;'
    tee =    '├──&nbsp;'
    last =   '└──&nbsp;'

    output = []

    dir_path = Path(root)  # accept strings coercible to Path
    files = 0
    directories = 0
    output.append('<div class="dir_tree">\n')
    def inner(dir_path: Path, prefix: str='', level=-1):
        """Yield one HTML-ready tree line per visible path.

        Args:
            dir_path: Directory currently being expanded.
            prefix: Visual tree prefix prepended to every emitted line.
            level: Remaining recursion depth.

        Yields:
            HTML-ready strings describing visible files and directories.
        """
        nonlocal files, directories
        if not level:
            return # 0, stop iterating
        contents = sorted(dir_path.iterdir(), key=lambda path: path.name.casefold())
        if limit_to_directories:
            contents = [path for path in contents if path.is_dir()]
        contents = [
            path for path in contents
            if not path.name.startswith(('.', NO_LINK_MARKER, IGNORE_MARKER))
            and path.name != ASSETS_FOLDER
        ]
        pointers = [tee] * (len(contents) - 1) + [last]
        for pointer, path in zip(pointers, contents):
            if path.is_dir():
                yield prefix + pointer + escape(path.name) + '/'
                directories += 1
                extension = branch if pointer == tee else space
                yield from inner(path, prefix=prefix+extension, level=level-1)
            elif not limit_to_directories:
                link_str = path.name
                if len(link_str) >= 3 and link_str[:2].isdigit() and link_str[2] == '_':
                    # regex equivalent: ^[0-9]{2}_
                    link_str = link_str[3:]
                yield prefix + pointer + anchor_str.format(
                    escape(quote(link_str, safe='/._-'), quote=True),
                    escape(path.name),
                )
                files += 1
    output.append(escape(dir_path.name) + '<br>\n')
    iterator = inner(dir_path, level=level)
    for line in islice(iterator, length_limit):
        output.append(line+'<br>\n')
    if next(iterator, None):
        output.append(f'... length_limit, {length_limit}, reached, counted:'+'<br>\n')
    output.append(f'\n<br>{directories} directories' + (f', {files} files' if files else '')+'<br>\n')
    output.append('</div>\n')
    return ''.join(output)

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
