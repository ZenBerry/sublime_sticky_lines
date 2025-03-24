import sublime
import sublime_plugin
import time
import threading
import textwrap
from html import escape

loopin = False
thread = None
window = None
view = None
kill_switch = False #phahahaha! >:D

class ViewListener(sublime_plugin.EventListener):
    def on_activated(self, incoming_view):
        global window
        global view
        print('View switched!')
        
        window = sublime.active_window()
        view = window.active_view()

# Uncomment this if you actively edit the plugin
#
# class FileSaveListener(sublime_plugin.EventListener):
#     def on_pre_save_async(self, view):
#         print('nooooo')
#         global loopin
#         global thread
#         if loopin == True:
#             loopin = False
#         if thread:
#             print(thread)
#             print()
#             print('Wait for it...')
#             thread.join()
#             print('K.O!')
#             print(thread)
#             print('Yoshumitsu wins!')
#             print()

def normalize_indentation(s: str) -> str:
    return textwrap.dedent(s).expandtabs()

def hey_arnold(): 
    global loopin
    global thread
    global window
    global view

    # Toddlers with LLMs present:

    print('Tata kata-kata kata-da!')

    def find_parent_function(code, top_viewer_line_number):
        parent_line_string = ""
        lines = code.splitlines()
        
        top_viewer_line_string = ""
        try:
            top_viewer_line_string = lines[top_viewer_line_number]
        except:
            top_viewer_line_string = lines[1]
        
        global counter #honestly, it works, I don't wanna touch it haha :D
        counter = 0

        def get_indentation(line_index):
            global counter
            counter = line_index
            line = lines[line_index]
            if line.strip() != "":  # Good line
                return len(line) - len(line.lstrip())
            elif line_index > 0:  # Empty line, look up
                return get_indentation(line_index - 1)      
            return 0  # Default indentation if everything is empty
    
        top_viewer_line_indentation = get_indentation(top_viewer_line_number)
        parent_line_number = -1
        for i in range(top_viewer_line_number, 0, -1):

            line = lines[i]
            temp_indentation = get_indentation(i)

            if temp_indentation < top_viewer_line_indentation:
                parent_line_number = counter
                parent_line_string = lines[parent_line_number]
                counter = 0
                break

        return [top_viewer_line_string, parent_line_string, parent_line_number]  

    prev_top = None
    parent_line_string = ""
    prev_parent_string = ""
    window = sublime.active_window()
    view = window.active_view()

    while loopin:
        top_viewer_line_number = view.rowcol(view.visible_region().begin())[0]+4 # Get the top visible line

        def magic(line_number_in_question):
            content = '''\n''' #WARNING: counting lines from 1 :D
            content += view.substr(sublime.Region(0, view.size()))
            content = normalize_indentation(content)
            linne = content.split('\n')

            escaped_top_viewer_line_string = escape(find_parent_function(content, line_number_in_question)[0])

            parent_line_string = find_parent_function(content, line_number_in_question)[1]
            escaped_parent_line_string = escape(parent_line_string)

            parent_line_number = find_parent_function(content, line_number_in_question)[2]
            
            leading_spaces_num = len(escaped_parent_line_string) - len(escaped_parent_line_string.lstrip(' '))
            leading_spaces = ""
            for i in range(leading_spaces_num):
                leading_spaces += '&nbsp;'

            html = '''<div>''' + leading_spaces + '''<a style='white-space: nowrap; color: var(--foreground);' href='subl:goto_line {"line":'''
            html += str(parent_line_number)
            html += '''}'>'''
            html += escaped_parent_line_string.strip() + '''</a></div>'''

            if line_number_in_question <= 5:
                html = ""
            if parent_line_string == "":
                html = ""

            return {"html" : html, "parent_line_number": parent_line_number}

        if (top_viewer_line_number != prev_top ):
            final_html = ""
            init_line_number = top_viewer_line_number
            while True:
                magic_res = magic(init_line_number)
                final_html = magic_res['html'] + final_html
                init_line_number = magic_res['parent_line_number']
                if magic_res['parent_line_number'] < 1:
                    break
            pop = view.text_point(top_viewer_line_number-4,0)
            view.show_popup(
                final_html,                                                                                             
                location=pop,
                max_width=1400,
                flags=16)

        prev_top = top_viewer_line_number
        prev_parent_string = parent_line_string

        time.sleep(0.001) 

        # Adjust time.sleep interval to save your CPU haha. 
        # There has to be a better way, but I don't see relevant event listeners for now. 
        # on_hover is the closest, but it won't fire on scroll. 
        # TODO: try playing with 'point' and 'hover_zone' parameters: https://www.sublimetext.com/docs/api_reference.html#sublime_plugin.EventListener.on_hover

    return

def plugin_loaded():  
    global thread

    thread = threading.Thread(target=hey_arnold, name="Piu Piu")
    thread.start()
    print(thread)

class boomCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        global loopin
        loopin = not loopin
        if loopin:
            plugin_loaded()
        else:
            view.hide_popup()
        
