import os
import sublime
import sublime_plugin
import time
import threading
import textwrap
from html import escape

enabled = False
coffee = False
fps = 300

thread = None
window = None
view = None

class toggleStickyCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        global enabled
        enabled = not enabled
        if enabled:
            plugin_loaded()
        else:
            view.hide_popup()

class ViewListener(sublime_plugin.EventListener):
    def on_activated(self, incoming_view):
        """
        Feeds Sticky with new data as you switch between tabs or windows
        """
        global window
        global view
        global coffee
        window = sublime.active_window()
        view = window.active_view()
        coffee = True
    def on_deactivated(self, incoming_view):
        global coffee
        coffee = True

class FileSaveListener(sublime_plugin.EventListener):
    def on_pre_save_async(self, view):
        """
        Checks if the file being saved is the same as the current script.
        If it is, it terminates the existing Sticky thread, ensuring that only one instance of the plugin is active at a time.
        Intended for internal use and fellow plugin devs ^^
        """
        if os.path.realpath(view.file_name()) != os.path.realpath(__file__):
            return
        global enabled
        global thread
        if enabled == True:
            enabled = False
        if thread:
            print("Sticky lines is going to kill a thread right now. See the results below:")
            thread.join()
            print(thread)

def sticky_main():
    global enabled
    global thread
    global window
    global view

    intro = True
    intro_text = 'Hello! ^_^ Start scrolling to see some sticky lines'
    intro_text_progress = ''
    intro_text_typing_delay = 2
    intro_text_final_delay = 120

    for i in range(intro_text_final_delay):
        intro_text += ' '

    prev_top = None
    parent_line_string = ""
    prev_parent_string = ""
    window = sublime.active_window()
    view = window.active_view()
    loop_count = 0

    def normalize_indentation(s: str) -> str:
        """
        Formats the raw string containing your current file's contents to find parents efficiently:
        Removes common leading whitespace from all lines using textwrap.dedent().
        Replaces tabs with spaces using .expandtabs()
        Don't worry, it does NOT modify your code haha.
        """
        return textwrap.dedent(s).expandtabs()

    def find_parent_function(code, top_viewer_line_number):
        parent_line_string = ""
        lines = code.splitlines()
        

        top_viewer_line_string = ""
        try: top_viewer_line_string = lines[top_viewer_line_number] 
        except: pass

        global counter #honestly, it works, I don't wanna touch it haha :D
        counter = 0

        def get_indentation(line_index):
            global counter
            counter = line_index

            line = ""
            try: line = lines[line_index]
            except: pass

            if line.strip() != "":  # Good line
                return len(line) - len(line.lstrip())
            elif line_index > 0:  # Empty line, look up
                return get_indentation(line_index - 1)
            return 0  # Default indentation if everything is empty

        top_viewer_line_indentation = get_indentation(top_viewer_line_number)
        parent_line_number = -1

        for i in range(top_viewer_line_number, 0, -1):
            try: line = lines[i]
            except: pass

            temp_indentation = get_indentation(i)

            if temp_indentation < top_viewer_line_indentation:
                parent_line_number = counter
                parent_line_string = ""
                try: parent_line_string = lines[parent_line_number]
                except: pass

                counter = 0
                break

        return [top_viewer_line_string, parent_line_string, parent_line_number]

    while enabled:
        global coffee
        top_viewer_line_number = view.rowcol(view.visible_region().begin())[0]+4 # Get the top visible line
        original_file = view.substr(sublime.Region(0, view.size()))

        if original_file == '':
            continue
        
        def magic(line_number_in_question):

            content = '''\n''' #WARNING: counting lines from 1 :D
            content += view.substr(sublime.Region(0, view.size()))
            content = normalize_indentation(content)

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

        if (top_viewer_line_number != prev_top or intro or coffee):
            global coffee
            if len(intro_text_progress) < len(intro_text):
                if loop_count % intro_text_typing_delay == 0:
                    intro_text_progress += intro_text[len(intro_text_progress)]
                    final_html = intro_text_progress
            else:
                intro = False
                final_html = ""
                init_line_number = top_viewer_line_number
                while True:
                    magic_res = magic(init_line_number)
                    final_html = magic_res['html'] + final_html
                    init_line_number = magic_res['parent_line_number']
                    if magic_res['parent_line_number'] < 1:
                        break
            view.show_popup(
                final_html,
                location=view.visible_region().begin(),
                max_width=1400,
                flags=16)
            coffee = False

        prev_top = top_viewer_line_number
        prev_parent_string = parent_line_string
        loop_count += 1

        time.sleep(1/fps)

        """
        Adjust fps to save your CPU haha.
        There has to be a better way, but I don't see relevant event listeners for now.
        on_hover is the closest, but it won't fire on scroll.
        TODO: try playing with 'point' and 'hover_zone' parameters: https://www.sublimetext.com/docs/api_reference.html#sublime_plugin.EventListener.on_hover
        """

    return

def plugin_loaded():
    global thread
    thread = threading.Thread(target=sticky_main, name="Sticky")
    thread.start()
    print(thread)






