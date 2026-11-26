from odoo.http import request

from odoo.addons.cooperator_website.controllers.main import WebsiteSubscription


class RecaptchaWebsiteSubscription(WebsiteSubscription):
    def _additional_validate(self, kwargs, logged, values, post_file):
        result = super()._additional_validate(kwargs, logged, values, post_file)
        if result is not True:
            return result
        result, error_msg = request.website.is_recaptcha_v2_valid(kwargs)
        if not result:
            values["error_msg"] = request.env._(
                "Error validating the CAPTCHA: %s", error_msg
            )
        return result
