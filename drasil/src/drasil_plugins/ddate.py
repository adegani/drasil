from ddate.base import DDate

class DrasilPlug():
    triggers = ['DDATE'ß]
    name = 'DDate' 
    description = 'Print the current date in discrodian format'
    help_str = 'The plugin has no args. When the trigger is found, prints the discordian date' 
    
    def pre(self, *argv):
        print('Nothing to pre')
        pass

    def run(self, *argv):
        return DDate()

    def post(self, *argv):
        print('Nothing to post')
        pass