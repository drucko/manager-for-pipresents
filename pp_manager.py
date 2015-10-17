#! /usr/bin/env python
import gui.gui as gui
import gui.server as serv
# import gui
#  from gui import *
import subprocess
import sys, os, shutil
import ConfigParser

class MyApp(gui.App):

    def __init__(self, *args):
        super(MyApp, self).__init__(*args)


    def idle(self):
        self.poll_pp()
        """ Usefull function to schedule tasks. 
        Called every configuration.UPDATE_ITERVAL """
        super(MyApp, self).idle()

    def print_paths(self):
        print 'home',self.pp_home_dir
        print 'profiles',self.pp_profiles_offset, self.pp_profiles_dir
        print 'media', self.media_offset, self.media_dir
        print 'top',self.top_dir


    def main(self):
        print 'Pi Presents Manager'
        # get directory holding the code
        self.manager_dir=sys.path[0]
            
        if not os.path.exists(self.manager_dir + os.sep + 'pp_manager.py'):
            print 'Pi Presents Manager - Bad Application Directory'
            exit()

        self.opt=Options()

        # create an options file if necessary
        self.options_file_path=self.manager_dir+os.sep+'pp_manager.cfg'
        if not os.path.exists(self.options_file_path):
            self.opt.create_options(self.options_file_path)

        # read the options
        self.get_options(self.options_file_path)

        # and construct the paths
        self.pp_profiles_dir=self.pp_home_dir+os.sep+'pp_profiles'+self.pp_profiles_offset
        self.media_dir=self.pp_home_dir+self.media_offset
        self.print_paths()

        #init variables
        self.profile_objects=[]
        self.current_profile=''
        self.pp_state='unknown'   # running-external, running-manager, not-running
        self.pp_proc=None # pi Presents subprocess object when started by pp_manager

        # root and frames
        # the arguments are width - height - layoutOrientationOrizontal
        root = gui.Widget(450, 600, False, 10)
        top_frame=gui.Widget(450,40,False,1)
        middle_frame=gui.Widget(450,500,False,1)
        button_frame=gui.Widget(250,40,True,10)

        # menu
        menu = gui.Menu(430, 20)
        
        # media menu
        media_menu = gui.MenuItem(50, 20, 'Media')
        
        media_copy_menu = gui.MenuItem(100, 30, 'Copy')
        media_copy_menu.set_on_click_listener(self, 'on_media_copy_clicked')
        
        media_upload_menu = gui.MenuItem(100, 30, 'Upload')
        media_upload_menu.set_on_click_listener(self, 'on_media_upload_clicked')

        #profile menu
        profile_menu = gui.MenuItem(50, 20, 'Profile')
        
        profile_copy_menu = gui.MenuItem(100, 30, 'Copy')
        profile_copy_menu.set_on_click_listener(self, 'on_profile_copy_clicked')
        
        profile_upload_menu = gui.MenuItem(100, 30, 'Upload')
        profile_upload_menu.set_on_click_listener(self, 'on_profile_upload_clicked')
        
        profile_download_menu = gui.MenuItem(100, 30, 'Download')
        profile_download_menu.set_on_click_listener(self, 'on_profile_download_clicked')
        
        #options menu
        options_menu = gui.MenuItem(50,20,'Options')
        
        profiles_option_menu = gui.MenuItem(100, 30, 'Profiles Offset')
        profiles_option_menu.set_on_click_listener(self, 'on_profiles_offset_option_menu_clicked')
        
        media_option_menu = gui.MenuItem(100, 30, 'Media Offset')
        media_option_menu.set_on_click_listener(self, 'on_media_offset_option_menu_clicked')

        autostart_option_menu = gui.MenuItem(100, 30, 'Autostart Profile')
        autostart_option_menu.set_on_click_listener(self, 'on_autostart_profile_option_menu_clicked')

        
        # list of profiles
        self.profile_list = gui.ListView(300, 300)
        self.profile_list.set_on_selection_listener(self,'on_profile_selected')

         
        #status and buttons

        self.profile_name = gui.Label(400, 20,'Current Profile: ')
        
        self.pp_state_display = gui.Label(400, 20,'Pi Presents is: ')
        
        self.run_pp = gui.Button(80, 30, 'Run')
        self.run_pp.set_on_click_listener(self, 'on_run_button_pressed')
        
        self.exit_pp = gui.Button(80, 30, 'Exit')
        self.exit_pp.set_on_click_listener(self, 'on_exit_button_pressed')
        
        self.status = gui.Label(400, 30, 'Last Action: Pi Presents Manager Started')
        
        self.profile_download=gui.FileDownloader(300,30,'Click to download current profile',self.current_profile)

        self.upload_dialog=gui.FileUploader(200,30,self.media_dir+os.sep)
        self.upload_dialog.set_on_success_listener(self,'on_media_upload_success')
        self.upload_dialog.set_on_failed_listener(self,'on_media_upload_failed')



        # Build the layout

        # buttons
        button_frame.append('0', self.run_pp)
        button_frame.append('1', self.exit_pp)

        # middle frame
        middle_frame.append('0',self.profile_name)
        middle_frame.append('1',self.pp_state_display)
        middle_frame.append('2',button_frame)
        middle_frame.append('3',self.profile_list)
        middle_frame.append('4', self.status)
        middle_frame.append('5',self.profile_download)
        middle_frame.append('6',self.upload_dialog)       

        # menus
        profile_menu.append('1',profile_copy_menu)
        profile_menu.append('2',profile_upload_menu)
        profile_menu.append('3',profile_download_menu)


        media_menu.append('1',media_copy_menu)
        media_menu.append('2',media_upload_menu)
        
        options_menu.append('0',media_option_menu)
        options_menu.append('1',autostart_option_menu)
        options_menu.append('2',profiles_option_menu)

        menu.append('1',profile_menu)
        menu.append('2',media_menu)
        menu.append('3',options_menu)
        
        top_frame.append('1',menu)
        
        root.append('1',top_frame)
        root.append('2',middle_frame)
        

        # display the initial list of profiles
        self.display_profiles()

        # this does not work here as it needs browser to be connected for it to start
        if self.autostart_profile != '':
            autostart_profile_path= self.pp_profiles_dir+os.sep+self.autostart_profile
            if not os.path.exists(autostart_profile_path):
                self.display_error('Profile does not exist: ' + autostart_profile_path)
            else:
                self.current_profile=self.pp_profiles_offset+os.sep+self.autostart_profile
                self.on_run_button_pressed()

        # returning the root widget
        return root



    # OPTIONS MENU EVENTS

    def on_profiles_offset_option_menu_clicked(self):
        self.inputDialog = gui.InputDialog('Options', 'Profiles Offset (advanced)',self.pp_profiles_offset)
        self.inputDialog.set_on_confirm_value_listener(
            self, 'on_profiles_offset_option_menu_confirm')
        self.inputDialog.show(self)
              
    def on_profiles_offset_option_menu_confirm(self,result):
        pp_profiles_offset = result
        pp_profiles_dir=self.pp_home_dir+os.sep+'pp_profiles'+pp_profiles_offset
        if not os.path.exists(pp_profiles_dir):
            self.update_status('FAILED: Edit Profile Offset')
            self.display_error('Path Invalid: ' + pp_profiles_dir)
        else:
            self.pp_profiles_offset = pp_profiles_offset
            self.opt.pp_profiles_offset = pp_profiles_offset
            self.pp_profiles_dir=pp_profiles_dir
            self.print_paths()
            self.opt.save_options(self.options_file_path)
            # and display the new lit of profiles
            self.display_profiles()
            self.update_status('Edit Profile Offset successful')

        
    def on_media_offset_option_menu_clicked(self):
        self.inputDialog = gui.InputDialog('Options', 'Pi Presents Media Location',self.media_offset)
        self.inputDialog.set_on_confirm_value_listener(
            self, 'on_media_offset_option_menu_confirm')
        self.inputDialog.show(self)
            
    def on_media_offset_option_menu_confirm(self,result):
        media_offset=result
        media_dir=self.pp_home_dir+media_offset
        if not os.path.exists(media_dir):
            self.update_status('FAILED: Edit Media Offset')
            self.display_error('Media Directory does not exist: ' + media_dir)
        else:
            self.media_offset=media_offset
            self.opt.media_offset=media_offset
            self.media_dir=media_dir
            self.opt.save_options(self.options_file_path)
            self.update_status('Edit Media Offset successful')


    def on_autostart_profile_option_menu_clicked(self):
        self.inputDialog = gui.InputDialog('Options', 'Autostart Profile',self.autostart_profile)
        self.inputDialog.set_on_confirm_value_listener(
            self, 'on_autostart_profile_option_menu_confirm')
        self.inputDialog.show(self)
            
    def on_autostart_profile_option_menu_confirm(self,result):
        autostart_profile=result
        autostart_profile_path=self.pp_profiles_dir+os.sep+autostart_profile
        if not os.path.exists(autostart_profile_path):
            self.update_status('FAILED: Edit Autostart Profile')
            self.display_error('Profile does not exist: ' + autostart_profile_path)
        else:
            self.autostart_profile=autostart_profile
            self.opt.autostart_profile=autostart_profile
            self.opt.save_options(self.options_file_path)
            self.update_status('Edit Autostart Profile successful')




    # PROFILES LIST and RUNNING PP
    def display_profiles(self):
        self.empty_profiles_list()
        items = os.listdir(self.pp_profiles_dir)
        i=0
        for item in items:
            obj= gui.ListItem(300, 20,item)
            self.profile_objects.append(obj)
            self.profile_list.append(i,obj)
            i+=1
        return

    def empty_profiles_list(self):
        for obj in self.profile_objects:
            self.profile_list.remove(obj)
        self.profile_objects=[]

    def on_profile_selected(self,key):
        self.current_profile_name=self.profile_list.children[key].get_text()
        self.current_profile=self.pp_profiles_offset + os.sep + self.current_profile_name
        self.profile_name.set_text('Current Profile: '+self.pp_profiles_offset+os.sep+self.current_profile_name)
        
    def on_run_button_pressed(self):
        if self.pp_proc == None:
            if self.current_profile != '':
                options_list= self.options.split(' ')
                command = ['python',self.command,'-p',self.current_profile]
                if options_list[0] != '':
                    command += options_list
                self.pp_proc=subprocess.Popen(command)
                self.pp_state='running-manager'
                self.update_status('Pi Presents Started')

       
    def on_exit_button_pressed(self):
        if self.pp_proc != None:
            self.pp_proc.terminate()
            self.pp_proc=None
            self.pp_state='not-running'
            self.update_status('Pi Presents Exited')


    def poll_pp(self):
        if self.pp_state == 'running-manager':
            self.pp_state_display.set_text( 'Pi Presents is: RUNNING')   
        else:
            self.pp_state_display.set_text( 'Pi Presents is: STOPPED ' )   

    """
            retcode=self.pp_proc.poll()
            if retcode == None:
                self.pp_state_display.set_text( 'Pi Presents is: RUNNING')   
            else:
                self.pp_proc=None
                self.pp_state_display.set_text( 'Pi Presents is: STOPPED ' + str(retcode))   
    """
  
    #MEDIA
    
     # copy  
    def on_media_copy_clicked(self):
        fileselectionDialog = gui.FileSelectionDialog('Copy Media', 'Select files to copy',multiple_selection = True, selection_folder = self.top_dir)
        fileselectionDialog.set_on_confirm_value_listener(self, 'on_media_copy_dialog_confirm')
        fileselectionDialog.set_on_abort_value_listener(self, 'on_media_copy_dialog_abort')
        fileselectionDialog.show(self)

    def on_media_copy_dialog_abort(self):
        self.update_status('Media copy cancelled: ')

    def on_media_copy_dialog_confirm(self, filelist):
        #a list() of filenames and folders is returned
        self.copy_list=filelist
        copy_from1=filelist[0]
        self.copy_to=self.media_dir
        if not copy_from1.startswith(self.top_dir):
            self.update_status('FAILED: Copy Media')
            self.display_error('Access to source prohibited: ' + copy_from1)
            return
        if not os.path.exists(self.copy_to):
            self.update_status('FAILED: Copy Media')
            self.display_error(' Media directory does not exist: ' + self.copy_to)
            return

        print self.copy_list, self.copy_to
        self.ok_cancel('Files will be ovewritten even if newer',self.copy_media_confirm)


    def copy_media_confirm(self,result):
        if result:
            for item in self.copy_list:
                if os.path.isdir(item):
                    self.update_status('FAILED: Copy Media')
                    self.display_error(' Cannot copy a directory: ' )
                else:
                    shutil.copy2(item, self.copy_to)
            self.update_status('Media copy sucessful: ')
        else:
            self.update_status('Media copy cancelled: ')


    # upload
    def on_media_upload_clicked(self):
        print 'media upload clicked'
        upload_dialog=gui.FileUploader(600,600,self.media_dir+os.sep)
        upload_dialog.set_on_success_listener(self,'on_media_upload_success')
        upload_dialog.set_on_failed_listener(self,'on_media_upload_failed')
        upload_dialog.show(self)
                                              

    def on_media_upload_success(self,result):
        self.update_status('Media Upload successful')


    def on_media_upload_failed(self,result):
        self.update_status('FAILED: Upload Media')
        self.display_error(' Media Upload Failed: ' + result )


        
    #PROFILES

    # copy
    def on_profile_copy_clicked(self):
        fileselectionDialog = gui.FileSelectionDialog('Copy Profile', 'Select a Profile to copy',multiple_selection = False, selection_folder = self.top_dir)
        fileselectionDialog.set_on_confirm_value_listener(self, 'on_profile_copy_dialog_confirm')
        fileselectionDialog.set_on_abort_value_listener(self, 'on_profile_copy_dialog_abort')
        fileselectionDialog.show(self)

    def on_profile_copy_dialog_abort(self):
        self.update_status('Profile copy cancelled: ')

    def on_profile_copy_dialog_confirm(self, filelist):
        self.copy_from=filelist[0]
        self.from_basename=os.path.basename(self.copy_from)
        self.copy_to=self.pp_profiles_dir+os.sep+self.from_basename
        print self.copy_from, self.copy_to, self.top_dir
        if not self.copy_from.startswith(self.top_dir):
            self.update_status('FAILED: Copy Profile')
            self.display_error('Access to source prohibited: ' + self.copy_from)
            return
        if not os.path.isdir(self.copy_from):
            self.update_status('FAILED: Copy Profile')
            self.display_error('Source is not a directory: ' + self.copy_from)
            return
        if not os.path.exists(self.copy_from + os.sep + 'pp_showlist.json'):
            self.update_status('FAILED: Copy Profile')
            self.display_error('Source is not a profile: ' + self.copy_from)
            return
        if os.path.exists(self.copy_to):
            self.ok_cancel('Existing profile will be deleted',self.copy_profile_confirm)
        else:
            self.copy_profile_confirm(True)


    def copy_profile_confirm(self,result):            
        if result:
            if os.path.exists(self.copy_to):
                shutil.rmtree(self.copy_to)
            print self.copy_from,self.copy_to
            shutil.copytree(self.copy_from, self.copy_to)
            self.empty_profile_list()
            self.profile_count=self.display_profiles()

            self.update_status('Profile copy successful: ')
        else:
            self.update_status('Profile copy cancelled: ')




    # upload    
    def on_profile_upload_clicked(self):
        self.update_status('NOT IMPLEMENTED YET: ')
        pass

    # download
    def on_profile_download_clicked(self):
        ffile = self.media_dir+os.sep+'twitter.doc'
        print 'profile download clicked',ffile
        profile_download=gui.FileDownloader(600,600,'Click to download current profile',self.current_profile)
        profile_download.show(self)
        print 'profile download complete'




        
# ERRORS and UTILITIES    

    # Display error dialog
    def display_error(self,text):
        inputDialog = gui.InputDialog('Pi Presents Web Control', 'Error',text)
        inputDialog.set_on_confirm_value_listener(self, 'on_display_error_confirm')
        inputDialog.show(self)

    def on_display_error_confirm(self,result):
        pass


    # ok/cancel dialog
    def ok_cancel(self,text,callback):
        self.ok_cancel_callback=callback
        inputDialog = gui.InputDialog('Pi Presents Web Control', text,'')
        inputDialog.set_on_confirm_value_listener(self, 'ok_cancel_confirm')
        inputDialog.set_on_abort_value_listener(self, 'ok_cancel_abort')
        inputDialog.show(self)

    def ok_cancel_confirm(self,result):
        self.ok_cancel_callback(True)

    def ok_cancel_abort(self):
            self.ok_cancel_callback(False)

    # Status

    def update_status(self,text):
        self.status.set_text('Last Action: '+ text)


# OPTIONS

     # veneer for MyApp class
    def get_options(self,path):
        self.opt.read_options(path)
        self.pp_home_dir =self.opt.pp_home_dir 
        self.pp_profiles_offset = self.opt.pp_profiles_offset
        self.media_offset = self.opt.media_offset
        self.top_dir =  self.opt.top_dir
        self.command = self.opt.command 
        self.options = self.opt.options
        self.autostart_profile = self.opt.autostart_profile
        

class Options(object):

    def read_options(self,options_file):
        """reads options from options file to interface"""
        config=ConfigParser.ConfigParser()
        config.read(options_file)
        
        self.pp_home_dir =config.get('config','home',0)
        self.pp_profiles_offset =config.get('config','profiles_offset',0)
        self.media_offset =config.get('config','media_offset',0)
        self.top_dir = config.get('config','top',0)
        self.command = config.get('config','program',0)
        self.options = config.get('config','options',0)
        self.autostart_profile=config.get('config','autostart')


    def create_options(self,options_file):
        config=ConfigParser.ConfigParser()
        config.add_section('config')
        if os.name == 'nt':
            config.set('config','home',os.path.expanduser('~')+'\pp_home')
            config.set('config','media_offset','\media')
            config.set('config','profiles_offset','')
            config.set('config','top',os.path.expanduser('~'))
            config.set('config','program','')
            config.set('config','options','')
            config.set('config','autostart','')
        else:
            config.set('config','home',os.path.expanduser('~')+'/pp_home')
            config.set('config','media_offset','/media')
            config.set('config','profiles_offset','')
            config.set('config','top',os.path.expanduser('~'))
            config.set('config','program','python /home/pi/pipresents/pipresents.py')
            config.set('config','options','')
            config.set('config','autostart','')
        with open(options_file, 'wb') as config_file:
            config.write(config_file)


    def save_options(self,options_file):
        """ save the output of the options edit dialog to file"""
        config=ConfigParser.ConfigParser()
        config.add_section('config')
        config.set('config','home',self.pp_home_dir)
        config.set('config','top',self.top_dir)
        config.set('config','media_offset',self.media_offset)
        config.set('config','profiles_offset',self.pp_profiles_offset)
        config.set('config','program',self.command)
        config.set('config','options',self.options)
        config.set('config','autostart',self.autostart_profile)
        with open(options_file, 'wb') as config_file:
            config.write(config_file)
    

# ***************************************
# MAIN
# ***************************************


if __name__  ==  "__main__":
    serv.start(MyApp)


