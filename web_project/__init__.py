
# from web_project.bootstrap import TemplateBootstrap
from web_project.template_helpers.theme import TemplateHelper
from django.conf import settings


class TemplateLayout:
    # Initialize the bootstrap files and page layout
    def init(self, context):
        # Init the Template Context using TEMPLATE_CONFIG

        # Set a default layout globally using settings.py. Can be set in the page level view file as well.
        layout = "vertical"

        # Set the selected layout
        context.update(
            {
                "layout_path": TemplateHelper.set_layout(
                    "layout_" + layout + ".html", context
                ),
            }
        )

        request = getattr(self, "request", None)
        if request and request.session.get("_impersonator_id"):
            context["is_impersonating"] = True
            display_name = getattr(request.user, "display_name", None) or getattr(
                request.user, "username", ""
            ) or getattr(request.user, "email", "")
            context["impersonated_user_name"] = display_name

        # Map context variables
        TemplateHelper.map_context(context)

        return context
