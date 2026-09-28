from netbox.plugins import PluginMenu, PluginMenuButton, PluginMenuItem

incident_item = PluginMenuItem(
    link='plugins:netbox_incidents:incident_list',
    link_text='Инциденты',
    permissions=['netbox_incidents.view_incident'],
    buttons=(
        PluginMenuButton(
            link='plugins:netbox_incidents:incident_add',
            title='Добавить',
            icon_class='mdi mdi-plus-thick',
            permissions=['netbox_incidents.add_incident'],
        ),
    ),
)

reports_item = PluginMenuItem(
    link='plugins:netbox_incidents:reports',
    link_text='Отчёты',
    permissions=['netbox_incidents.view_incident'],
)

menu = PluginMenu(
    label='База инцидентов',
    icon_class='mdi mdi-alert-decagram-outline',
    groups=(
        ('Инциденты', (incident_item,)),
        ('Отчёты', (reports_item,)),
    ),
)
