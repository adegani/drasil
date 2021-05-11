from datetime import datetime

class DrasilPlug():
    hooks = ['today']
    name = 'Today' 
    description = 'Print the current date YYYY-MM-DD'
    help_str = 'The plugin has no args. When the trigger is found, prints the current date' 
    
    def pre(self, *argv):
        pass

    def run(self, *argv):
        return datetime.today().strftime('%Y-%m-%d')

    def post(self, *argv):
        pass