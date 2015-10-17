"""
   Licensed under the Apache License, Version 2.0 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.
"""

import gui
from gui import *


class MyApp(App):

    def __init__(self, *args):
        super(MyApp, self).__init__(*args)

    def main(self):
        # the arguments are	width - height - layoutOrientationOrizontal
        wid = gui.Widget(120, 100, False, 10)
        self.lbl = gui.Label(100, 30, 'Hello world!')
        self.bt = gui.Button(100, 30, 'Press me!')

        # setting the listener for the onclick event of the button
        self.bt.set_on_click_listener(self, 'on_button_pressed')

        # appending a widget to another, the first argument is a string key
        wid.append('1', self.lbl)
        wid.append('2', self.bt)

        # returning the root widget
        return wid

    # listener function
    def on_button_pressed(self):
        self.lbl.set_text('Button pressed!')
        self.bt.set_text('Hi!')


# starts the webserver
start(MyApp)
