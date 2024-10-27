import json


class SettingsManager:
    def __init__(self):
        self.settings_file = 'settings.json'
        self.template_file = 'template.json'

    def load_settings(self):
        try:
            with open(self.settings_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            default_settings = {"check_mode": "exact"}
            self.save_settings(default_settings)
            return default_settings

    def save_settings(self, settings):
        with open(self.settings_file, 'w', encoding='utf-8') as f:
            json.dump(settings, f, indent=4)

    def load_template(self):
        with open(self.template_file, 'r', encoding='utf-8') as f:
            return json.load(f)

    def reload_templates(self):
        with open(self.template_file, 'r', encoding='utf-8') as f:
            self.template = json.load(f)
        return self.template