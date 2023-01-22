# Artist-Util extension for AUTOMATIC1111/stable-diffusion-webui
#
# https://github.com/tkalayci71/artist-util
# version 1.0 - 2023.01.23

import gradio as gr
from modules.script_callbacks import on_ui_tabs
from modules.scripts import basedir
from os import path, scandir, makedirs
from PIL import Image

BASE_FOLDER = path.join(basedir(),'')
DATA_FOLDER = path.join(BASE_FOLDER,'data','')

#-------------------------------------------------------------------------------
# Options
#-------------------------------------------------------------------------------

NUM_IMAGES = 4
IMAGE_PER_ROW = 4

SHOW_ASSORTED = False # True
RIGHT_ALIGN_ASSORTED = False # True

HTML_ADD_INDEX = False # True
HTML_BORDER_STR = '0' # '1'
HTML_WIDTH_STR = '128'
HTML_HEIGHT_STR = '128'
HTML_ADD_TAGS = True # False # True
HTML_ADD_ASSORTED = False # True

#-------------------------------------------------------------------------------
# Utils
#-------------------------------------------------------------------------------

def make_sure_dir_exists(dir_name):
    if not path.exists(dir_name):
        makedirs(dir_name)
    if not path.exists(dir_name):
        raise

def get_folder_list(dir_name):
    if not path.exists(dir_name):
        return []
    result = []
    for it in scandir(dir_name):
        if it.is_dir():
            result.append(it.name)
    return result

def get_file_list(dir_name, ext='', remove_ext=False):
    if not path.exists(dir_name):
         return []
    result = []
    for it in scandir(dir_name):
        if it.is_file():
            if ext!='':
                if not it.name.endswith('.'+ext):
                    continue
            file_name = it.name
            if remove_ext:
                file_name = path.splitext(file_name)[0]
            result.append(file_name)
    return result

def load_string_list(file_name, process=False, addempty=False):
    if not path.exists(file_name):
        return []
    result=[]
    with open(file_name,encoding='utf-8') as f:
        lines = f.readlines()
        for line in lines:
            line = line.replace('\n','')
            line = line.strip()
            if (addempty==True) or (line!=''):
                result.append(line)
        f.close()
    if process:
        result = [x.lower() for x in result]
        old_len = len(result)
        result = list(dict.fromkeys(result))
        new_len = len(result)
        if (old_len!=new_len):
            print('warning : ignoring ',str(new_len-old_len),' duplicates in ',file_name)
        result.sort()
    return result

def save_string_list(string_list, file_name, overwrite):
    if path.exists(file_name):
        if overwrite==False:
            return
    with open(file_name,'w',encoding='utf-8',) as f:
        f.writelines('\n'.join(string_list))
        f.close()
    return

def get_list_index(source_list, item, is_list_sorted=False):
    try:
        found_index = source_list.index(item)
    except:
        found_index = -1
    return found_index

#-------------------------------------------------------------------------------
# AuEngine class
#-------------------------------------------------------------------------------

class AuEngine:

    SPECIAL_ALL = '- All -'
    SPECIAL_NOTAG = '- Uncategorized -'

    def __init__(self, data_folder):

        self.data_folder = data_folder
        make_sure_dir_exists(self.data_folder)
        self.images_folder = path.join(self.data_folder,'images','')
        make_sure_dir_exists(self.images_folder)
        self.tags_folder = path.join(self.data_folder,'tags','')
        make_sure_dir_exists(self.tags_folder)
        self.assorted_folder = path.join(self.data_folder,'assorted','')
        make_sure_dir_exists(self.assorted_folder)

        if (SHOW_ASSORTED==True) or (HTML_ADD_ASSORTED==True):
            self.assorted_images = get_file_list(self.assorted_folder)
        else:
            self.assorted_images = []

        self.image_subfolder_choices = get_folder_list(self.images_folder)
        self.image_subfolder_choices.sort()

        self.image_files = {}
        for subfolder in self.image_subfolder_choices:
            file_list = get_file_list(path.join(self.images_folder,subfolder,''))
            file_list.sort()
            self.image_files[subfolder] = file_list

        self.tag_choices = get_file_list(self.tags_folder,ext='txt',remove_ext=True)
        self.tag_choices.sort()

        self.tag_data = {}
        for tag_name in self.tag_choices:
            self.tag_data[tag_name]=load_string_list(path.join(self.tags_folder,tag_name+'.txt'),process=True)

        self.template_choices = load_string_list(path.join(self.data_folder,'templates.txt'),process=False)

        self.all_names_list = load_string_list(path.join(self.data_folder,'names.txt'),process=True)

        self.list_choices = [self.SPECIAL_ALL, self.SPECIAL_NOTAG]+ self.tag_choices
        self.selected_list = ''
        self.selected_list_index = -1

        self.name_choices = []
        self.selected_name = ''
        self.selected_name_index = -1
        self.default_name_indexes = {}

    def select_list(self, item):
        found_index = get_list_index(self.list_choices, item)
        if found_index==-1:
            self.selected_list = ''
            self.selected_list_index = -1
            self.name_choices = []
            self.selected_name = ''
            self.selected_name_index = -1
            return

        self.selected_list = self.list_choices[found_index]
        self.selected_list_index = found_index

        #update name_choices
        if item==self.SPECIAL_ALL:
            self.name_choices = self.all_names_list.copy()
        elif item==self.SPECIAL_NOTAG:
            self.name_choices = self.get_uncategorized_names()
        else:
            self.name_choices = []
            tag_data = self.tag_data.get(item,None)
            if tag_data!=None:
                for n in range(len(self.all_names_list)):
                    name = self.all_names_list[n]
                    if name in tag_data:
                        self.name_choices.append(name)
        self.select_name(None)

    def select_name(self, item):
        found_index = get_list_index(self.name_choices, item)
        if found_index==-1:
            self.selected_name = ''
            self.selected_name_index = -1
            return
        self.selected_name = self.name_choices[found_index]
        self.selected_name_index = found_index
        if self.selected_list_index!=-1:
            self.default_name_indexes[self.selected_list] = found_index

    def get_default_template(self):
        if len(self.template_choices)>0:
            default_template = self.template_choices[0]
        else:
            default_template = ''
        return default_template

    def get_default_list(self):
        if len(self.list_choices)>0:
            default_list = self.list_choices[0]
        else:
            default_list = ''
        return default_list

    def get_default_name(self):
        if self.selected_list_index==-1:
            return ''
        index = self.default_name_indexes.get(self.selected_list,-1)
        if index==-1:
            if len(self.name_choices)>0: index = 0
        if (index<0) or (index>=len(self.name_choices)):
            default_name = ''
        else:
            default_name=self.name_choices[index]
        return default_name

    def get_name_tags(self, name):
        if name=='': return []
        result = []
        for n in range(len(self.tag_choices)):
            tag_name = self.tag_choices[n]
            tag_data = self.tag_data[tag_name]
            if (name in tag_data):
                result.append(tag_name)
        return result

    def set_name_tags(self, name, new_tags):
        for n in range(len(self.tag_choices)):
            tag_name = self.tag_choices[n]
            tag_data = self.tag_data[tag_name]
            old_checked = name in tag_data
            new_checked = tag_name in new_tags
            if (old_checked!=new_checked):
                if new_checked:
                    tag_data.append(name)
                else:
                    tag_data.remove(name)
                tag_data.sort()
                save_string_list(tag_data, path.join(self.tags_folder,tag_name+'.txt'),overwrite=True)

    def get_uncategorized_names(self):
        result = []
        for n in range(len(self.all_names_list)):
            name = self.all_names_list[n]
            found = False
            for i in range(len(self.tag_choices)):
                tag_name = self.tag_choices[i]
                tag_data = self.tag_data[tag_name]
                if (name in tag_data):
                    found = True
                    break
            if found==False:
                result.append(name)
        return result

    def load_image(self, image_sub_folder, name):
        name = name.strip().lower()
        if (name=='') or (image_sub_folder==''): return None
        result = None
        image_files = self.image_files.get(image_sub_folder,None)
        if image_files==None: return None
        for file_name in image_files:
            if name in file_name.lower():
                image_path = path.join(self.images_folder,image_sub_folder,'')
                image_fnam = path.join(image_path,file_name)
                try:
                    result = Image.open(image_fnam)
                    break
                except:
                    print('warning: error loading ',image_fnam)
        return result

    def save_last_folders(self,folders):
        save_string_list(folders, path.join(self.data_folder,'last_folders.txt'),overwrite=True)

    def load_last_folders(self):
        folders = load_string_list(path.join(self.data_folder,'last_folders.txt'),process=False,addempty=True)
        num_folders = len(folders)
        if (num_folders>0) and (num_folders<NUM_IMAGES):
                folders = folders + ['']*(NUM_IMAGES-num_folders)
        return folders

    def get_assorted_images(self, name):
        name = name.strip().lower()
        if name=='':
            return []
        result = []
        for file_name in self.assorted_images:
            if name in file_name.lower():
                image_fnam = path.join(self.assorted_folder,file_name)
                img = None
                try:
                    img = Image.open(image_fnam)
                except:
                    img = None
                    print('warning: error loading ',image_fnam)
                if img!=None:
                    result.append(img)
        return result

    def find_image_filename(self, image_sub_folder, name):
        name = name.strip().lower()
        if (name=='') or (image_sub_folder==''): return None
        result = None
        image_files = self.image_files.get(image_sub_folder,None)
        if image_files==None: return None
        for file_name in image_files:
            if name in file_name.lower():
                result = file_name
                break
        return result

    def get_assorted_filenames(self, name):
        name = name.strip().lower()
        if name=='':
            return []
        result = []
        for file_name in self.assorted_images:
            if name in file_name.lower():
                result.append(file_name)
        return result

#-------------------------------------------------------------------------------
# UI actions
#-------------------------------------------------------------------------------

def do_list_selector_change(new_selected_list):
    au.select_list(new_selected_list)
    au.select_name(au.get_default_name())
    name_selector_update = gr.Dropdown.update(choices=au.name_choices, value=au.selected_name)
    name_tags_update = gr.CheckboxGroup.update(value=au.get_name_tags(au.selected_name))
    selected_name_update = au.selected_name
    return [name_selector_update,name_tags_update,selected_name_update]

def do_name_selector_change(new_selected_name):
    au.select_name(new_selected_name)
    name_tags_update = gr.CheckboxGroup.update(value=au.get_name_tags(au.selected_name))
    selected_name_update = au.selected_name
    return [name_tags_update, selected_name_update]

def do_prev_name_button_click():
    cur_index = au.selected_name_index
    prev_index = cur_index-1
    if prev_index<0:
        name_selector_update = gr.Dropdown.update()
        name_tags_update = gr.CheckboxGroup.update()
    else:
        au.select_name(au.name_choices[prev_index])
        name_selector_update = gr.Dropdown.update(value=au.selected_name)
        name_tags_update = gr.CheckboxGroup.update(value=au.get_name_tags(au.selected_name))
    selected_name_update = gr.Textbox.update(value=au.selected_name)
    return [name_selector_update,name_tags_update,selected_name_update]

def do_next_name_button_click():
    cur_index = au.selected_name_index
    next_index = cur_index+1
    if next_index>=len(au.name_choices):
        name_selector_update = gr.Dropdown.update()
        name_tags_update = gr.CheckboxGroup.update()
    else:
        au.select_name(au.name_choices[next_index])
        name_selector_update = gr.Dropdown.update(value=au.selected_name)
        name_tags_update = gr.CheckboxGroup.update(value=au.get_name_tags(au.selected_name))
    selected_name_update = gr.Textbox.update(value=au.selected_name)
    return [name_selector_update,name_tags_update,selected_name_update]

def do_name_tags_change(new_tags):
    if au.selected_name_index==-1: return
    au.set_name_tags(au.selected_name,new_tags)
    return

def do_find_first_button_click(search_text):
    search_text = search_text.strip().lower()
    if search_text=='':
        name_selector_update = gr.Dropdown.update()
        name_tags_update = gr.CheckboxGroup.update()
    else:
        found_name = None
        for n in range(len(au.name_choices)):
            name = au.name_choices[n]
            if search_text in name:
                found_name = name
                break
        if (found_name==None):
            name_selector_update = gr.Dropdown.update(value='')
            name_tags_update = gr.CheckboxGroup.update(value=[])
        elif (found_name==au.selected_name):
            name_selector_update = gr.Dropdown.update()
            name_tags_update = gr.CheckboxGroup.update()
        else:
            au.select_name(found_name)
            name_selector_update = gr.Dropdown.update(value=au.selected_name)
            name_tags_update = gr.CheckboxGroup.update(value=au.get_name_tags(au.selected_name))

    selected_name_update = gr.Textbox.update(value=au.selected_name)
    return [name_selector_update,name_tags_update,selected_name_update]

def do_find_next_button_click(search_text):
    search_text = search_text.strip().lower()
    if search_text=='':
        name_selector_update = gr.Dropdown.update()
        name_tags_update = gr.CheckboxGroup.update()
    else:
        cur_index = au.selected_name_index
        found_name = None
        for n in range(cur_index+1,len(au.name_choices)):
            name = au.name_choices[n]
            if search_text in name:
                found_name = name
                break
        if (found_name==None):
            name_selector_update = gr.Dropdown.update()
            name_tags_update = gr.CheckboxGroup.update()
        else:
            au.select_name(found_name)
            name_selector_update = gr.Dropdown.update(value=au.selected_name)
            name_tags_update = gr.CheckboxGroup.update(value=au.get_name_tags(au.selected_name))

    selected_name_update = gr.Textbox.update(value=au.selected_name)
    return [name_selector_update,name_tags_update,selected_name_update]

def do_save_button_click(template_text,prompt_text,skip_tags):
    #prompt_text = prompt_text.lower()
    results = []
    log = []
    log.append('Template: "'+template_text+'"')
    log.append('Prompt: "'+prompt_text+'"')
    log.append('List: "'+au.selected_list+'"')
    num_skipped = 0
    for n in range(len(au.name_choices)):
        name = au.name_choices[n]
        if len(skip_tags)>0:
            name_tags = au.get_name_tags(name)
            found = False
            for tag_name in name_tags:
                if tag_name in skip_tags:
                    found = True
                    break
            if found:
                num_skipped+=1
                continue
        text = template_text.replace('NAME',name).replace('PROMPT',prompt_text)
        text = text.replace('NAME',name)
        results.append(text)
    if len(skip_tags)>0:
        log.append('List contains '+str(len(au.name_choices))+' names')
        log.append('Skip tags: '+str(skip_tags))
        log.append('Skipped '+str(num_skipped)+' names')

    log.append('Generated prompts for '+str(len(results))+' names')
    if len(results)>0:
        full_path = path.join(BASE_FOLDER,'output.txt')
        try:
            save_string_list(results, full_path,True)
            log.append('Saved '+full_path)
        except Exception as e:
            log.append('Error: could not save '+full_path+'\n'+str(e))
    log_text = '\n'.join(log)
    return log_text

def do_selected_name_change(selected_name,*folder_selectors):
    folder_images = []
    for n in range(len(folder_selectors)):
        folder = folder_selectors[n]
        img = au.load_image(folder, selected_name)
        folder_images.append(img)
    if SHOW_ASSORTED==True:
        assorted_images= au.get_assorted_images(selected_name)
        assorted_gallery_update = gr.Gallery.update(value=assorted_images)
    else:
        assorted_gallery_update = gr.Gallery.update()
    total_result = [assorted_gallery_update]+folder_images
    if len(total_result)==1:
        total_result = total_result[0]
    return total_result

def do_folder_selector_change(selected_name,selected_folder, *all_folders):
    img=au.load_image(selected_folder, selected_name)
    au.save_last_folders(all_folders)
    return img

def do_save_html(*image_folders):
    r = []
    r.append('<html>')
    r.append('<head></head>')
    r.append('<body>')

    r.append('<table border='+HTML_BORDER_STR+'>')
    r.append('  <tr>')

    if HTML_ADD_INDEX==True:
        r.append('    <th></th>')
    r.append('    <th>Name</th>')
    for f in range(len(image_folders)):
        folder = image_folders[f]
        if folder=='': continue
        r.append('    <th>'+folder+'</th>')
    if HTML_ADD_TAGS==True:
        r.append('    <th>Tags</th>')

    if HTML_ADD_ASSORTED==True:
        r.append('    <th>Other</th>')

    r.append('  </tr>')

    for n in range(len(au.name_choices)):
        r.append('  <tr>')
        name = au.name_choices[n]
        if HTML_ADD_INDEX==True:
            r.append('    <td>'+str(n)+'</td>')
        r.append('    <td>'+name+'</td>')

        for f in range(len(image_folders)):
            folder = image_folders[f]
            if folder=='': continue
            img_name = au.find_image_filename(folder,name)
            if img_name==None:
                r.append('    <td></td>')
            else:
                img_path = 'data/images/'+folder+'/'+img_name
                r.append('    <td>'+'<img src="'+img_path+
                    '" width='+HTML_WIDTH_STR+', height='+HTML_HEIGHT_STR+'>'+'</td>')

        if HTML_ADD_TAGS==True:
            tag_list = au.get_name_tags(name)
            tag_str = str(tag_list)
            r.append('    <td>'+tag_str+'</td>')

        if HTML_ADD_ASSORTED==True:

            files = au.get_assorted_filenames(name)
            all_files = []
            for file in files:
                file_path = 'data/assorted/'+file
                all_files.append('<img src="'+file_path+
                '" width='+HTML_WIDTH_STR+', height='+HTML_HEIGHT_STR+'>')
            total_str=''.join(all_files)
            r.append('    <td>'+total_str+'</td>')

        r.append('  </tr>')
    r.append('</table>')
    r.append('</body>')
    r.append('</html>')

    log = []
    full_path = path.join(BASE_FOLDER,'html_output.html')
    try:
        save_string_list(r,full_path,overwrite=True)
        log.append('Saved '+full_path)
    except Exception as e:
        log.append('Error: could not save '+full_path+'\n'+str(e))

    log_text = '\n'.join(log)
    return log_text

#-------------------------------------------------------------------------------
# Create UI
#-------------------------------------------------------------------------------

au : AuEngine = None

def add_tab():

    if not path.exists(BASE_FOLDER):
        print('Error: base folder does not exist '+BASE_FOLDER)
        raise
    global au
    au = AuEngine(DATA_FOLDER)

    with gr.Blocks(analytics_enabled=False) as ui:
        with gr.Row():

            with gr.Column(scale=1):
                with gr.Row():
                    au.select_list(au.get_default_list())
                    list_selector = gr.Dropdown(label='Browse', choices=au.list_choices, value=au.selected_list)

                with gr.Row():
                    au.select_name(au.get_default_name())
                    name_selector = gr.Dropdown(label='Name', choices=au.name_choices, value=au.selected_name)

                with gr.Row():
                    prev_name_button = gr.Button(value='prev')
                    next_name_button = gr.Button(value='next')


            with gr.Column(scale=2):
                    with gr.Accordion(label='Categorize',open=True):
                        with gr.Row():
                            selected_name = gr.Textbox(value=au.selected_name,label='Selected Name',show_label=False,lines=1,max_lines=1,interactive=False)
                        with gr.Row():
                            name_tags = gr.CheckboxGroup(label='Tags',choices=au.tag_choices,value=au.get_name_tags(au.selected_name))

            with gr.Column(scale=1):

                with gr.Accordion(label='Find',open=True):
                    with gr.Row():
                        search_text = gr.Textbox(label='Text',lines=1,max_lines=1)
                    with gr.Row():
                        find_first_button = gr.Button(value='first')
                        find_next_button = gr.Button(value='next')

            with gr.Column(scale=1):

                with gr.Accordion(label='Generate prompts',open=False):

                    with gr.Row():
                        template_selector = gr.Dropdown(label='Template',choices=au.template_choices, value=au.get_default_template)
                    with gr.Row():
                        prompt_text = gr.Textbox(label='Prompt',lines=2,max_lines=2)

                    with gr.Row():
                        with gr.Accordion(label='Skip',open=False):
                            skip_tags = gr.CheckboxGroup(label='Tags',choices=au.tag_choices)

                    with gr.Row():
                        save_button = gr.Button(value='Save TXT')
                    with gr.Row():
                        log_text = gr.Textbox(label='Log',lines=2,interactive=False)

                with gr.Accordion(label='Export HTML',open=False):
                    with gr.Row():
                        html_button = gr.Button('Save HTML')
                    with gr.Row():
                        html_log = gr.Textbox(label='Log',lines=2,interactive=False)

        with gr.Row():

            def add_assorted():
                if SHOW_ASSORTED==True:
                    with gr.Column(scale=1):
                        assorted_images= au.get_assorted_images(au.selected_name)
                        assorted_gallery = gr.Gallery(label='Assorted', show_label=False, value =assorted_images)
                else:
                    assorted_gallery = gr.Gallery(visible=False)
                return assorted_gallery

            def add_image_folders():
                folder_selectors=[]
                folder_images=[]
                NUM_IMAGE_ROWS = NUM_IMAGES//IMAGE_PER_ROW
                if IMAGE_PER_ROW*NUM_IMAGE_ROWS < NUM_IMAGES: NUM_IMAGE_ROWS+=1
                last_folders = au.load_last_folders()
                with gr.Column(scale=IMAGE_PER_ROW):
                    for row_no in range(NUM_IMAGE_ROWS):
                        with gr.Row():
                            for col_no in range(IMAGE_PER_ROW):
                                with gr.Column():
                                    image_no = row_no*IMAGE_PER_ROW + col_no
                                    if image_no<NUM_IMAGES:
                                            if len(last_folders)==0:
                                                folder = au.image_subfolder_choices[image_no] if image_no<len(au.image_subfolder_choices) else ''
                                            else:
                                                folder = last_folders[image_no]
                                                if not folder in au.image_subfolder_choices: folder = ''
                                            with gr.Row():
                                                img = au.load_image(folder,au.selected_name)
                                                fi = gr.Image(show_label=False, interactive=False, value=img)
                                                folder_images.append(fi)
                                            with gr.Row():
                                                fs = gr.Dropdown(show_label=False, choices=['']+au.image_subfolder_choices, value=folder)
                                                folder_selectors.append(fs)
                return folder_selectors, folder_images


            if RIGHT_ALIGN_ASSORTED==True:
                folder_selectors, folder_images = add_image_folders()
                assorted_gallery = add_assorted()
            else:
                assorted_gallery = add_assorted()
                folder_selectors, folder_images = add_image_folders()

        # actions
        list_selector.change(fn=do_list_selector_change,inputs=list_selector,outputs=[name_selector,name_tags,selected_name])
        name_selector.change(fn=do_name_selector_change,inputs=name_selector,outputs=[name_tags,selected_name])
        prev_name_button.click(fn=do_prev_name_button_click,outputs=[name_selector,name_tags,selected_name])
        next_name_button.click(fn=do_next_name_button_click,outputs=[name_selector,name_tags,selected_name])
        name_tags.change(fn=do_name_tags_change,inputs=name_tags)
        find_first_button.click(fn=do_find_first_button_click,inputs=search_text,outputs=[name_selector,name_tags,selected_name])
        find_next_button.click(fn=do_find_next_button_click,inputs=search_text,outputs=[name_selector,name_tags,selected_name])
        save_button.click(fn=do_save_button_click,inputs=[template_selector,prompt_text,skip_tags],outputs=log_text)
        html_button.click(fn=do_save_html,inputs=folder_selectors, outputs=html_log)

        selected_name.change(fn=do_selected_name_change,inputs=[selected_name]+folder_selectors,outputs=[assorted_gallery]+folder_images)
        for n in range(len(folder_selectors)):
            folder_selector=folder_selectors[n]
            folder_selector.change(fn=do_folder_selector_change,inputs=[selected_name,folder_selector]+folder_selectors,outputs=folder_images[n])

    return [(ui, "Artist-Util", "artist_util")]

on_ui_tabs(add_tab)

#-------------------------------------------------------------------------------

