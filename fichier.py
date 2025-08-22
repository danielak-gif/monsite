from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager, Screen
from kivymd.app import MDApp
from kivymd.uix.button import MDRaisedButton, MDFlatButton
from kivy.uix.boxlayout import BoxLayout
from kivymd.uix.textfield import MDTextField
from kivy.uix.label import Label
from kivy.clock import Clock
from kivy.animation import Animation
from kivy.core.window import Window
from kivy.garden.matplotlib.backend_kivyagg import FigureCanvasKivyAgg

import sympy as sp
from sympy.printing.latex import latex
import matplotlib.pyplot as plt
import numpy as np

# -------------------- Classes Python -------------------- #
class MenuScreen(Screen):
    pass

class BaseTab(Screen):
    current_textfield = None
    preview_event = None
    keyboard_visible = False

    def on_focus(self, instance, value):
        if value:
            BaseTab.current_textfield = instance
            self.show_keyboard(animated=True)
        else:
            BaseTab.current_textfield = None
            self.hide_keyboard(animated=True)

    def show_keyboard(self, animated=False):
        try:
            kb = self.ids.scientific_keyboard
            if animated:
                anim = Animation(height=200, opacity=1, duration=0.3)
                anim.start(kb)
            else:
                kb.height = 200
                kb.opacity = 1
            BaseTab.keyboard_visible = True
        except:
            pass

    def hide_keyboard(self, animated=False):
        try:
            kb = self.ids.scientific_keyboard
            if animated:
                anim = Animation(height=0, opacity=0, duration=0.3)
                anim.start(kb)
            else:
                kb.height = 0
                kb.opacity = 0
            BaseTab.keyboard_visible = False
        except:
            pass

    def insert_text(self, text):
        if BaseTab.current_textfield:
            cursor = BaseTab.current_textfield.cursor_index()
            s = BaseTab.current_textfield.text
            BaseTab.current_textfield.text = s[:cursor] + text + s[cursor:]
            BaseTab.current_textfield.cursor = (cursor + len(text), 0)
            self.schedule_preview()

    def insert_fraction(self):
        if BaseTab.current_textfield:
            cursor = BaseTab.current_textfield.cursor_index()
            s = BaseTab.current_textfield.text
            insert_text = r"\frac{}{}"
            BaseTab.current_textfield.text = s[:cursor] + insert_text + s[cursor:]
            BaseTab.current_textfield.cursor = (cursor + 6, 0)
            self.schedule_preview()

    def insert_sqrt(self):
        if BaseTab.current_textfield:
            cursor = BaseTab.current_textfield.cursor_index()
            s = BaseTab.current_textfield.text
            insert_text = r"\sqrt{}"
            BaseTab.current_textfield.text = s[:cursor] + insert_text + s[cursor:]
            BaseTab.current_textfield.cursor = (cursor + 6, 0)
            self.schedule_preview()

    def insert_power(self):
        if BaseTab.current_textfield:
            cursor = BaseTab.current_textfield.cursor_index()
            s = BaseTab.current_textfield.text
            insert_text = r"^{}"
            BaseTab.current_textfield.text = s[:cursor] + insert_text + s[cursor:]
            BaseTab.current_textfield.cursor = (cursor + 2, 0)
            self.schedule_preview()

    def create_scientific_keyboard(self, keyboard_id):
        from functools import partial
        buttons = [
            ['sin(', 'cos(', 'tan('],
            ['asin(', 'acos(', 'atan('],
            ['sinh(', 'cosh(', 'tanh('],
            ['exp(', 'ln(', 'log('],
            ['√', 'a/b', '^']
        ]
        keyboard_box = self.ids[keyboard_id]
        keyboard_box.clear_widgets()
        for row in buttons:
            box = BoxLayout(spacing=5)
            for btn in row:
                if btn == '√':
                    b = MDRaisedButton(text=btn, on_release=partial(self.insert_sqrt))
                elif btn == 'a/b':
                    b = MDRaisedButton(text=btn, on_release=partial(self.insert_fraction))
                elif btn == '^':
                    b = MDRaisedButton(text=btn, on_release=partial(self.insert_power))
                else:
                    b = MDRaisedButton(text=btn, on_release=lambda inst, t=btn: self.insert_text(t))
                box.add_widget(b)
            keyboard_box.add_widget(box)

    def schedule_preview(self, dt=0):
        if self.preview_event:
            self.preview_event.cancel()
        self.preview_event = Clock.schedule_once(self.update_preview, 0.5)

    def update_preview(self, dt=0):
        if not BaseTab.current_textfield:
            return
        expr_str = BaseTab.current_textfield.text.strip()
        container = self.ids.result_box
        container.clear_widgets()
        if expr_str == "":
            return
        try:
            expr_str_mod = expr_str.replace('√','sqrt').replace('a/b', '(1/1)')  # fraction placeholder
            expr = sp.sympify(expr_str_mod)
            fig, ax = plt.subplots(figsize=(5,1))
            ax.axis('off')
            ax.text(0.5, 0.5, f"${latex(expr)}$", ha='center', va='center', fontsize=18)
            container.add_widget(FigureCanvasKivyAgg(fig))
        except:
            container.add_widget(Label(text="Erreur syntaxe"))

# -------------------- Tabs spécialisées -------------------- #
class AnalyseTab(BaseTab):
    def on_kv_post(self, base_widget):
        self.create_scientific_keyboard('scientific_keyboard')

    def calculate(self):
        Window.release_keyboard()
        expr_str = self.ids.expr_input.text.replace('√','sqrt').replace('a/b','(1/1)')
        try:
            expr = sp.sympify(expr_str)
            result = sp.simplify(expr)
            self.update_preview()
        except Exception as e:
            self.ids.result_box.clear_widgets()
            self.ids.result_box.add_widget(Label(text=f"Erreur: {e}"))

class AlgebreTab(BaseTab):
    def on_kv_post(self, base_widget):
        self.create_scientific_keyboard('scientific_keyboard')

    def calculate(self):
        from sympy import Matrix
        try:
            mat = sp.sympify(self.ids.matrix_input.text)
            M = Matrix(mat)
            result = M.eigenvals()
            self.update_preview_text(str(result))
        except Exception as e:
            self.update_preview_text(f"Erreur: {e}")

    def update_preview_text(self, text):
        self.ids.result_box.clear_widgets()
        self.ids.result_box.add_widget(Label(text=text))

class FinanceTab(BaseTab):
    def on_kv_post(self, base_widget):
        self.create_scientific_keyboard('scientific_keyboard')

    def calculate(self):
        try:
            VA = float(self.ids.va_input.text)
            i = float(self.ids.i_input.text)
            t = float(self.ids.t_input.text)
            VF = VA*(1+i)**t
            self.update_preview_text(f"VF = {VF:.2f}")
        except Exception as e:
            self.update_preview_text(f"Erreur: {e}")

    def update_preview_text(self, text):
        self.ids.result_box.clear_widgets()
        self.ids.result_box.add_widget(Label(text=text))

class GraphTab(BaseTab):
    def on_kv_post(self, base_widget):
        self.create_scientific_keyboard('scientific_keyboard')

    def calculate(self):
        expr_str = self.ids.expr_input.text.replace('√','sqrt').replace('a/b','(1/1)')
        x = sp.Symbol('x')
        container = self.ids.result_box
        container.clear_widgets()
        try:
            expr = sp.sympify(expr_str)
            x_vals = np.linspace(-10,10,400)
            y_vals = []
            for val in x_vals:
                try:
                    y = float(expr.subs(x,val))
                    y_vals.append(y)
                except:
                    y_vals.append(np.nan)
            fig, ax = plt.subplots()
            ax.plot(x_vals, y_vals)
            ax.grid(True)
            ax.set_title(expr_str)
            container.add_widget(FigureCanvasKivyAgg(fig))
        except Exception as e:
            container.add_widget(Label(text=f"Erreur: {e}"))

# -------------------- KV -------------------- #
KV = '''
ScreenManager:
    MenuScreen:
    AnalyseTab:
    AlgebreTab:
    FinanceTab:
    GraphTab:

<MenuScreen>:
    name: 'menu'
    MDBoxLayout:
        orientation: 'vertical'
        spacing: dp(10)
        padding: dp(20)
        MDLabel:
            text: "Calculatrice Pro - Math Avancée"
            halign: "center"
            font_style: "H4"
        MDRaisedButton:
            text: "Analyse"
            on_release: root.manager.current='analyse'
        MDRaisedButton:
            text: "Algèbre"
            on_release: root.manager.current='algebre'
        MDRaisedButton:
            text: "Finance"
            on_release: root.manager.current='finance'
        MDRaisedButton:
            text: "Graphiques"
            on_release: root.manager.current='graph'

<AnalyseTab>:
    name: 'analyse'
    MDBoxLayout:
        orientation: 'vertical'
        padding: dp(10)
        spacing: dp(10)
        MDTextField:
            id: expr_input
            hint_text: "Ex: sin(x)**2, a/b, √(x)"
            on_focus: root.on_focus(self, self.focus)
            on_text: root.schedule_preview()
        BoxLayout:
            id: result_box
            size_hint_y: 0.35
        BoxLayout:
            id: scientific_keyboard
            orientation: 'vertical'
            size_hint_y: 0.4
            height: 0
            opacity: 0
        MDRaisedButton:
            text: "Calculer"
            on_release: root.calculate()
        MDFlatButton:
            text: "Retour"
            on_release: root.manager.current='menu'

<AlgebreTab>:
    name: 'algebre'
    MDBoxLayout:
        orientation: 'vertical'
        padding: dp(10)
        spacing: dp(10)
        MDTextField:
            id: matrix_input
            hint_text: "Ex: [[1,2],[3,4]]"
            on_focus: root.on_focus(self, self.focus)
        BoxLayout:
            id: result_box
            size_hint_y: 0.35
        BoxLayout:
            id: scientific_keyboard
            orientation: 'vertical'
            size_hint_y: 0.4
            height:0
            opacity:0
        MDRaisedButton:
            text: "Calculer"
            on_release: root.calculate()
        MDFlatButton:
            text: "Retour"
            on_release: root.manager.current='menu'

<FinanceTab>:
    name: 'finance'
    MDBoxLayout:
        orientation: 'vertical'
        padding: dp(10)
        spacing: dp(10)
        MDTextField:
            id: va_input
            hint_text: "Valeur actuelle (VA)"
        MDTextField:
            id: i_input
            hint_text: "Taux d'intérêt (i)"
        MDTextField:
            id: t_input
            hint_text: "Temps (t)"
        BoxLayout:
            id: result_box
            size_hint_y: 0.35
        BoxLayout:
            id: scientific_keyboard
            orientation: 'vertical'
            size_hint_y:0.4
            height:0
            opacity:0
        MDRaisedButton:
            text: "Calculer"
            on_release: root.calculate()
        MDFlatButton:
            text: "Retour"
            on_release: root.manager.current='menu'

<GraphTab>:
    name: 'graph'
    MDBoxLayout:
        orientation: 'vertical'
        padding: dp(10)
        spacing: dp(10)
        MDTextField:
            id: expr_input
            hint_text: "Ex: sin(x), x**2+3"
            on_focus: root.on_focus(self, self.focus)
            on_text: root.schedule_preview()
        BoxLayout:
            id: result_box
            size_hint_y:0.35
        BoxLayout:
            id: scientific_keyboard
            orientation:'vertical'
            size_hint_y:0.4
            height:0
            opacity:0
        MDRaisedButton:
            text:"Tracer"
            on_release: root.calculate()
        MDFlatButton:
            text:"Retour"
            on_release: root.manager.current='menu'
'''

# -------------------- App -------------------- #
class CalculatriceApp(MDApp):
    def build(self):
        self.theme_cls.primary_palette = "Blue"
        return Builder.load_string(KV)

if __name__ == "__main__":
    CalculatriceApp().run()
