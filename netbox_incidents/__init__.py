from netbox.plugins import PluginConfig


class NetBoxIncidentsConfig(PluginConfig):
    name = 'netbox_incidents'
    verbose_name = 'NetBox Incidents'
    description = 'Учёт инцидентов по устройствам, интерфейсам, модулям и стойкам — отдельно от Journal Entries.'
    version = '1.0.0'
    author = 'Zhakhongir Mirzayev'
    base_url = 'incidents'
    min_version = '4.6.0'
    default_settings = {
        # Slug группы контактов (tenancy.Contact), из которой выбирается "Контактное лицо".
        # Оставьте пустым (''), чтобы разрешить выбор из всех контактов.
        'contact_group_slug': '',
    }


config = NetBoxIncidentsConfig
