import unittest
from stapy import StapyPluginsAdapter
from stapy import StapyPlugins
from stapy import StapyFileSystem
from stapy import StapyParser
from stapy import StapyJsonQuery
from stapy import StapyEncoder
from stapy import StapyGenerator


plugins = StapyPluginsAdapter()
file_system = StapyFileSystem(plugins)
encoder = StapyEncoder()
json_query = StapyJsonQuery(file_system, encoder)
parser = StapyParser(plugins, file_system, json_query, encoder)
generator = StapyGenerator(file_system, json_query, parser)
plugins.set(StapyPlugins(file_system, json_query, parser, generator))


class TestServer(unittest.TestCase):

    def test_environments(self):
        environments = file_system.get_environments()
        self.assertTrue(environments)
        self.assertIn('local', environments)

    def test_file_extension(self):
        self.assertEqual(file_system.get_file_extension('index.html'), 'html')
        self.assertEqual(file_system.get_file_extension('index.html.json'), 'json')

    def test_file_type(self):
        self.assertIn(file_system.get_file_type('index.html'), 'text/html')
        self.assertIn(file_system.get_file_type('index.html.json'), 'application/json')

    def test_page_data(self):
        # Template var
        self.assertIn('template', file_system.get_page_data('/index.html'))
        # Common default config
        data = file_system.get_page_data('/index.html')
        self.assertIn('common', data)
        self.assertEqual(data['common'], 'false')
        data = file_system.get_page_data('/child.html')
        self.assertIn('common', data)
        self.assertEqual(data['common'], 'true')
        # Directory default config
        data = file_system.get_page_data('/index.html')
        self.assertEqual(data['subdir'], "")
        data = file_system.get_page_data('/foo/index.html')
        self.assertEqual(data['subdir'], "foo")
        data = file_system.get_page_data('/foo/bar/index.html')
        self.assertEqual(data['subdir'], "bar")
        data = file_system.get_page_data('/foo/bar/index.xml')
        self.assertEqual(data['subdir'], "common")
        # Plugin
        self.assertIn('plugin', data)
        self.assertEqual(data['plugin'], 'ok')
        # Path slash
        self.assertEqual(
            file_system.get_page_data('/index.html'),
            file_system.get_page_data('index.html')
        )

    def test_template_engine_var(self):
        self.assertEqual(parser.process({'foo': 'bar'}, '{{ foo }}', 'local'), 'bar')
        self.assertEqual(parser.process({'foo': 'bar'}, '{{ foo }} {{ foo }}', 'local'), 'bar bar')
        self.assertEqual(parser.process({'foo.prod': 'bar'}, '{{ foo }}', 'local'), '')
        self.assertEqual(parser.process({'foo.prod': 'bar'}, '{{ foo }}', 'prod'), 'bar')
        self.assertEqual(parser.process({'foo.local': 'bar'}, '{{ foo }}', 'local'), 'bar')

    def test_template_engine_tpl(self):
        # {{ title }}
        data = file_system.get_page_data('/index.html')
        self.assertIn('template', data)
        # {% content %}
        tpl = file_system.get_source_dir(data['template'])
        self.assertTrue(tpl)
        content = file_system.get_file_content(tpl)
        self.assertEqual(content, '{% content %}')
        self.assertEqual(parser.process(data, content, 'local'), 'It works!')
        self.assertEqual(parser.process(data, content, 'devel'), 'It works!')
        self.assertEqual(parser.process(data, content, 'prod'), 'It works in prod!')
        self.assertEqual(parser.process(data, content, 'staging'), '')

    def test_template_engine_tpl_child(self):
        # {% child_block + child/data %}
        data = file_system.get_page_data('/child.html')
        self.assertIn('template', data)
        # {% content %}
        tpl = file_system.get_source_dir(data['template'])
        self.assertTrue(tpl)
        content = file_system.get_file_content(tpl)
        self.assertEqual(content, '{% content %}')
        self.assertEqual(
            parser.process(data, content, 'local'),
            'Hello John :) How are you?\nHello John :) How are you?\nIt works! \nIt works! Good job'
        )
        self.assertEqual(
            parser.process(data, content, 'prod'),
            'Hello Jane :) How are you?\nHello Jane :) How are you?\nIt works! \nIt works! Good job'
        )
        self.assertEqual(parser.process(data, content, 'staging'), '\n\nIt works! \nIt works! Good job')

    def test_template_reserved_vars(self):
        data = file_system.get_page_data('/foo/index.html')
        self.assertIn('template', data)
        tpl = file_system.get_source_dir(data['template'])
        self.assertTrue(tpl)
        self.assertEqual(parser.process(data, '{{ _path }}', 'local'), 'foo/')
        self.assertEqual(parser.process(data, '{{ _full_path }}', 'local'), 'foo/index.html')
        self.assertEqual(parser.process(data, '{{ _env }}', 'local'), 'local')
        self.assertEqual(parser.process(data, '{{ _env }}', 'prod'), 'prod')

    def test_json_query(self):
        # Search
        self.assertEqual(len(json_query.fetch('')), 12)

        self.assertEqual(len(json_query.fetch('SELECT ITEMS WHERE query_test = "1"')), 1)
        self.assertEqual(len(json_query.fetch('SELECT ITEMS WHERE query_test="1"')), 1)
        self.assertEqual(len(json_query.fetch('SELECT ITEMS WHERE   query_test  =  "1"  ')), 1)
        self.assertEqual(len(json_query.fetch('select items where query_test = "1" or query_test = "2"')), 2)
        self.assertEqual(
            len(json_query.fetch('sEleCT   iTeEM wheRE (  query_test="1") oR   query_test =\'2\'')), 2
        )
        self.assertEqual(
            len(json_query.fetch('WHERE query_test = "1" OR query_test = "2"')), 2
        )
        self.assertEqual(
            len(json_query.fetch('WHERE query_test = "1" OR query_test = "2" SELECT ITEMS 1')), 1
        )

        self.assertEqual(len(json_query.fetch('SELECT ITEMS WHERE "foobar" in tags')), 0)
        self.assertEqual(len(json_query.fetch('SELECT ITEMS WHERE \'test\' in tags')), 2)
        self.assertEqual(len(json_query.fetch('SELECT ITEMS WHERE "my tag" in tags')), 1)
        self.assertEqual(len(json_query.fetch('SELECT ITEMS WHERE \'my tag\' in tags')), 1)
        self.assertEqual(len(json_query.fetch('SELECT ITEMS WHERE \'"quoted tag"\' in tags')), 1)
        self.assertEqual(len(json_query.fetch('SELECT ITEMS WHERE "\\"quoted tag\\"" in tags')), 1)

        self.assertEqual(len(json_query.fetch('SELECT ITEMS WHERE boolean_search = true')), 1)
        self.assertEqual(len(json_query.fetch('SELECT ITEMS WHERE boolean_search = false')), 0)

        self.assertEqual(len(json_query.fetch('SELECT ITEMS WHERE integer_search = 20')), 1)
        self.assertEqual(len(json_query.fetch('SELECT ITEMS WHERE integer_search = "20"')), 0)
        self.assertEqual(len(json_query.fetch('SELECT ITEMS WHERE integer_search > 19')), 1)
        self.assertEqual(len(json_query.fetch('SELECT ITEMS WHERE integer_search < 21')), 1)
        self.assertEqual(len(json_query.fetch('SELECT ITEMS WHERE integer_search > 20')), 0)
        self.assertEqual(len(json_query.fetch('SELECT ITEMS WHERE integer_search >= 20')), 1)
        self.assertEqual(len(json_query.fetch('SELECT ITEMS WHERE integer_search <= 20')), 1)
        self.assertEqual(len(json_query.fetch('SELECT ITEMS WHERE integer_search < 20')), 0)
        self.assertEqual(len(json_query.fetch('SELECT ITEMS WHERE integer_search > 100')), 0)

        self.assertEqual(len(json_query.fetch('SELECT ITEMS WHERE float_search = 19.9')), 1)
        self.assertEqual(len(json_query.fetch('SELECT ITEMS WHERE float_search = "19.9"')), 0)
        self.assertEqual(len(json_query.fetch('SELECT ITEMS WHERE float_search > 19.8')), 1)
        self.assertEqual(len(json_query.fetch('SELECT ITEMS WHERE float_search < 20')), 1)
        self.assertEqual(len(json_query.fetch('SELECT ITEMS WHERE float_search > 19.9')), 0)
        self.assertEqual(len(json_query.fetch('SELECT ITEMS WHERE float_search >= 19.9')), 1)
        self.assertEqual(len(json_query.fetch('SELECT ITEMS WHERE float_search <= 19.9')), 1)
        self.assertEqual(len(json_query.fetch('SELECT ITEMS WHERE float_search < 19.9')), 0)
        self.assertEqual(len(json_query.fetch('SELECT ITEMS WHERE float_search > 100')), 0)

        self.assertEqual(len(json_query.fetch('SELECT ITEMS WHERE 1 in list_search')), 0)
        self.assertEqual(len(json_query.fetch('SELECT ITEMS WHERE 2 in list_search')), 1)
        self.assertEqual(len(json_query.fetch('SELECT ITEMS WHERE "2" in list_search')), 0)
        self.assertEqual(len(json_query.fetch('SELECT ITEMS WHERE "2" in list_search OR 2 in list_search')), 1)

        self.assertEqual(len(json_query.fetch('SELECT ITEMS WHERE empty_search = ""')), 1)
        self.assertEqual(len(json_query.fetch('SELECT ITEMS WHERE empty_search != ""')), 0)
        self.assertEqual(len(json_query.fetch('SELECT ITEMS WHERE empty_search = \'\'')), 1)
        self.assertEqual(len(json_query.fetch('SELECT ITEMS WHERE empty_search != \'\'')), 0)

        self.assertEqual(
            len(json_query.fetch('SELECT ITEMS WHERE boolean_search = false OR integer_search = 20')),
            1
        )
        self.assertEqual(
            len(json_query.fetch('SELECT ITEMS WHERE boolean_search = true AND "test" in tags')),
            1
        )
        self.assertEqual(
            len(json_query.fetch('SELECT ITEMS WHERE (query_test = "1" OR query_test = "2") AND "test" in tags')),
            2
        )

        # Limit
        self.assertEqual(len(json_query.fetch('SELECT ITEMS 1-1 WHERE "test" in tags')), 1)
        self.assertEqual(len(json_query.fetch('SELECT ITEMS 1 WHERE "test" in tags')), 1)
        self.assertEqual(len(json_query.fetch('SELECT ITEMS 2 WHERE "test" in tags')), 1)
        self.assertEqual(len(json_query.fetch('SELECT ITEMS 1-2 WHERE "test" in tags')), 2)
        self.assertEqual(len(json_query.fetch('SELECT ITEMS 2-10 WHERE "test" in tags')), 1)
        self.assertEqual(len(json_query.fetch('SELECT ITEMS 3-10 WHERE "test" in tags')), 0)

        # Sort Order
        self.assertEqual(json_query.fetch('SELECT ITEMS 1 WHERE "test" in tags')[0][1]['query_test'], '2')
        self.assertEqual(
            json_query.fetch('SELECT ITEMS 1 WHERE "test" in tags ORDER BY query_test asc')[0][1]['query_test'], '1'
        )
        self.assertEqual(
            json_query.fetch('SELECT ITEMS 1 WHERE "test" in tags ORDER BY query_test desc')[0][1]['query_test'], '2'
        )
        self.assertEqual(
            json_query.fetch('ORDER BY query_test desc WHERE "test" in tags SELECT ITEMS 1')[0][1]['query_test'], '2'
        )

    def test_template_engine_tpl_query(self):
        # {% query_block ~ tags:test query_test:asc 1:10 %}
        data = file_system.get_page_data('/query.html')
        self.assertIn('template', data)
        # {% content %}
        tpl = file_system.get_source_dir(data['template'])
        self.assertTrue(tpl)
        content = file_system.get_file_content(tpl)
        self.assertEqual(
            parser.process(data, content, 'local'),
            '1 / 2 I\'m ~ "happy"\n2 / 2 I\'m ~ "happy"\n2 / 2 \n1 / 2  - \n2 / 2 '
        )

    def test_template_plugin_directive(self):
        # {: plugin_directive :}
        data = file_system.get_page_data('/plugin.html')
        self.assertIn('template', data)
        self.assertIn('content', data)
        tpl = file_system.get_source_dir(data['template'])
        self.assertTrue(tpl)
        content = file_system.get_file_content(tpl)
        self.assertEqual(
            parser.process(data, content, 'staging'),
            'Default!\nbar John " Doe Simple \' Quote I\'m :"Very \'Happy\'" I\'m :"Very \'Angry\'"  +:~"\'\nSpecific\n'
        )
        self.assertEqual(
            parser.process(data, content, 'local'),
            'Local!\nbar John " Doe Simple \' Quote I\'m :"Very \'Happy\'" I\'m :"Very \'Angry\'"  +:~"\'\nSpecific\n'
        )
        self.assertEqual(
            parser.process(data, content, 'prod'),
            'Prod!\nbar John " Doe Simple \' Quote I\'m :"Very \'Happy\'" I\'m :"Very \'Angry\'"  +:~"\'\nSpecific\n'
        )

    def test_expression_syntax(self):
        # {% block.syntax %}
        data = file_system.get_page_data('/syntax.html')
        self.assertIn('template', data)
        # {% content %}
        tpl = file_system.get_source_dir(data['template'])
        self.assertTrue(tpl)
        content = file_system.get_file_content(tpl)
        self.assertEqual(
            parser.process(data, content, 'local'),
            'okok ok\nok\nok\nok\nok\nok\nok\nok\nok\n    ok\n{% block.syntax %}'
        )

    def test_infinite_loop(self):
        # {% block.loop %}
        data = file_system.get_page_data('/loop.html')
        self.assertIn('template', data)
        # {% content %}
        tpl = file_system.get_source_dir(data['template'])
        self.assertTrue(tpl)
        content = file_system.get_file_content(tpl)
        self.assertEqual(parser.process(data, content, 'local'), 'Loop')

    def test_inception(self):
        data = file_system.get_page_data('/inception.html')
        tpl = file_system.get_source_dir(data['template'])
        content = file_system.get_file_content(tpl)
        self.assertEqual(parser.process(data, content, 'local'), 'Hello Dom Cobb')

    def test_all_tags(self):
        data = file_system.get_page_data('/tags.html')
        tpl = file_system.get_source_dir(data['template'])
        content = file_system.get_file_content(tpl)
        self.assertEqual(
            parser.process(data, content, 'local'),
            ('go ~ I\'m +  where:"here" + " and:\'you + him/her\'?\n' * 14).strip('\n')
        )


if __name__ == '__main__':
    unittest.main()
