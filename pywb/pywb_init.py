import handlers
import indexreader
import archivalrouter
import os
import yaml
import config_utils
import logging
import proxy

#=================================================================
DEFAULT_HEAD_INSERT = 'ui/head_insert.html'
DEFAULT_QUERY = 'ui/query.html'
DEFAULT_SEARCH = 'ui/search.html'
DEFAULT_INDEX = 'ui/index.html'
DEFAULT_ERROR = 'ui/error.html'


#=================================================================
## Reference non-YAML config
#=================================================================
def pywb_config_manual(config = {}):

    routes = []

    hostpaths = config.get('hostpaths', ['http://localhost:8080'])

    # collections based on cdx source
    collections = config.get('collections', {'pywb': './sample_archive/cdx/'})

    for name, value in collections.iteritems():
        route_config = config

        if isinstance(value, dict):
            # if a dict, extend with base properies
            index_paths = value['index_paths']
            value.update(route_config)
            route_config = value
        else:
            index_paths = str(value)

        cdx_source = indexreader.IndexReader.make_best_cdx_source(index_paths, **config)

        wb_handler = config_utils.create_wb_handler(
            cdx_source = cdx_source,
            archive_paths = route_config.get('archive_paths', './sample_archive/warcs/'),
            head_html = route_config.get('head_insert_html', DEFAULT_HEAD_INSERT),
            query_html = route_config.get('query_html', DEFAULT_QUERY),
            search_html = route_config.get('search_html', DEFAULT_SEARCH),
        )

        logging.info('Adding Collection: ' + name)

        route_class = route_config.get('route_class', None)
        if route_class:
            route_class = config_utils.load_class(route_class)
        else:
            route_class = archivalrouter.Route

        routes.append(route_class(name, wb_handler, filters = route_config.get('filters', [])))

        # cdx query handler
        if route_config.get('enable_cdx_api', False):
            routes.append(archivalrouter.Route(name + '-cdx', handlers.CDXHandler(cdx_source)))


    if config.get('debug_echo_env', False):
        routes.append(archivalrouter.Route('echo_env', handlers.DebugEchoEnvHandler()))

    if config.get('debug_echo_req', False):
        routes.append(archivalrouter.Route('echo_req', handlers.DebugEchoHandler()))


    static_routes = config.get('static_routes', {'static/default': 'static/'})

    for static_name, static_path in static_routes.iteritems():
        routes.append(archivalrouter.Route(static_name, handlers.StaticHandler(static_path)))

    # Check for new proxy mode!
    if config.get('enable_http_proxy', False):
        router = proxy.ProxyArchivalRouter
    else:
        router = archivalrouter.ArchivalRouter

    # Finally, create wb router
    return router(
        routes,
        # Specify hostnames that pywb will be running on
        # This will help catch occasionally missed rewrites that fall-through to the host
        # (See archivalrouter.ReferRedirect)
        hostpaths = hostpaths,

        abs_path = config.get('absolute_paths', True),

        home_view = config_utils.load_template_file(config.get('home_html', DEFAULT_INDEX), 'Home Page'),
        error_view = config_utils.load_template_file(config.get('error_html', DEFAULT_ERROR), 'Error Page')
    )



#=================================================================
# YAML config loader
#=================================================================
DEFAULT_CONFIG_FILE = 'config.yaml'


def pywb_config(config_file = None):
    if not config_file:
        config_file = os.environ.get('PYWB_CONFIG', DEFAULT_CONFIG_FILE)

    config = yaml.load(open(config_file))

    return pywb_config_manual(config)


import utils
if __name__ == "__main__" or utils.enable_doctests():
    # Just test for execution for now
    #pywb_config(os.path.dirname(os.path.realpath(__file__)) + '/../config.yaml')
    pywb_config_manual()

