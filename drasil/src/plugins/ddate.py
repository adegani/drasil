from ddate.base import DDate

class DrasilPlug():
    hooks = ['DDATE']
    name = 'DDate' 
    description = 'Print the current date in discordian format'
    help_str = 'The plugin has no args. When the trigger is found, prints the discordian date' 
    
    def pre(self, *argv):
        print('Nothing to pre')
        pass

    def run(self, *argv):
        return str(DDate()).replace('Today is', '')

    def post(self, *argv):
        print('Nothing to post')
        pass