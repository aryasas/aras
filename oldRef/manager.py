import typing as t
import logging

from flask import json
from flask import redirect
from flask import url_for
from flask import render_template
from flask import flash
from flask import make_response
from flask import jsonify
from flask import request
from flask import current_app

from flask.views import View
from flask.views import MethodView

from flask_login import current_user

from sqlalchemy.exc import SQLAlchemyError
from marshmallow import ValidationError

from werkzeug.wrappers import Response

from arasCore.lib.db import db
from arasCore.lib.base import BaseClass
from arasCore.lib.utils import Utilities as ut
from arasCore.lib.forms import DataSearchForm
from arasCore.lib.uploads import upload_image_file

from abc import abstractmethod

logger = logging.getLogger(__name__)


class BaseView(BaseClass):
    """Base of all view class.
    This contains very standard that can be used to make view.
    This shouldn't be inherit directly to make a view.
    """

    app = None
    main_title = None
    title = None
    endpoint = None
    url = None
    param = None

    def __init__(self, *args: t.Any, **kwargs: t.Any):
        logger.debug(f"BaseView Init : {self.__class__.__name__}")

        self.set_attributes(**kwargs)

    @abstractmethod
    def register_routes(self, *args: t.Any, **kwargs: t.Any):
        logger.debug(f"Base register routes [function] from : {self.__class__.__name__}")
        return


class RoutesMixin(BaseView):
    """Class to make a route.
    This contains very standard attr that can be used to make route.
    This shouldn't be inherit directly to make a view.
    """

    simple: t.Optional[bool] = None
    api: t.Optional[bool] = None
    child = None

    def __init__(self, *args: t.Any, **kwargs: t.Any):
        logger.debug(f"RouteMixin Init : {self.__class__.__name__}")
        BaseView.__init__(self, *args, **kwargs)
        logger.debug(f"routesmixin endpoint : {self.endpoint}")

        self.param_view = self.make_endpoint(*args, **kwargs)
        self.param_view_api = self.make_api_endpoint(*args, **kwargs)

    @staticmethod
    def resp(data, code) -> Response:
        return make_response(jsonify(json.loads(data)), code)

    def make_endpoint(self, *args: t.Any, **kwargs: t.Any) -> dict:

        endpoint = self.endpoint

        view_endpoint = {
            "list_view_name": endpoint,
            "add_view_name": f"{endpoint}_add",
            "edit_view_name": f"{endpoint}_edit",
            "delete_view_name": f"{endpoint}_delete",
        }

        self.param_view = view_endpoint

        return self.param_view

    def make_api_endpoint(self, *args: t.Any, **kwargs: t.Any) -> dict:

        endpoint = self.endpoint

        view_endpoint = {
            "api_list_view_name": f"{endpoint}_api",
            "api_add_view_name": f"{endpoint}_add_api",
            "api_edit_view_name": f"{endpoint}_edit_api",
            "api_delete_view_name": f"{endpoint}_delete_api",
        }

        self.param_view_api = view_endpoint

        return self.param_view_api

    def register_routes(self, *args: t.Any, **kwargs: t.Any):
        logger.debug(f"RouteMixin register routes [function] from : {self.__class__.__name__}")
        self.as_view(*args, **kwargs)

        if self.simple:
            view_name = self.endpoint
            self.app.add_url_rule(
                self.url,
                view_func=self.as_view(
                    name=view_name, title=self.title, app=self.app, *args, **kwargs
                ),
            )
        else:
            pass


class ViewMixin(RoutesMixin, View):
    """Basic view class to make a view.
    This contains very basic attribute(including from BaseView needed to create page.
    Can directly inherited for simple view. Example Use:
    """

    template = None
    extends_layout = None
    param_menu = []
    gmenu = []
    crud: t.Optional[bool] = None

    def __init__(self, *args: t.Any, **kwargs: t.Any):
        logger.debug(f"ViewMixin Init : {self.__class__.__name__}")
        RoutesMixin.__init__(self, *args, **kwargs)

    def register_routes(self, *args: t.Any, **kwargs: t.Any):
        return

    def admin_endpoint_request(self):
        return str(request.path).__contains__("admin")

    def admin_layout(self, extends_layout) -> bool:
        return extends_layout if self.admin_endpoint_request() else None

    def render(self, template="", *args: t.Any, **kwargs: t.Any):
        logger.debug(f"ViewMixin Render : {self.__class__.__name__}")
        return render_template(
            template,
            main_title=self.main_title,
            title=self.title,
            param=self.param,
            param_menu=self.param_menu,
            gmenu=self.gmenu,
            extends_layout=self.extends_layout,
            *args,
            **kwargs,
        )


class CrudView(ViewMixin):
    """
    TODO: CrudView: Masih harus di evaluasi dan diperbaiki
    Must refactor!
    """

    # template for list view
    list_template = None or "admin/adm_list.html"
    # template for detail view
    form_template = None or "admin/adm_form.html"
    # template for child detail view in parent form
    list_detail_template = None or "admin/adm_list_detail.html"

    model = None
    schema = None
    form = None
    # explicitly define view column
    view_columns: list = []
    exclude_column: list = []
    # set if want to sort data
    order_column = None
    order_type = None

    sort_by_user = None

    # set if have media
    media = None
    # set if want to paginate
    have_pagination = None

    # parameter needed for view
    param: dict = {}
    param_view: dict = {}

    """If data is parent data, these 3 parameter must filled"""
    parent = None
    have_child = None
    # child form
    child_forms = None
    # column link to child
    link_columns: list = []
    # TRIAL
    child_class = None
    # parameter for parent view if have_child
    param_view_child_for_parent: list = []

    """If data is child data, these 3 parameter must filled"""
    # parent endpoint
    parent_endpoint = None
    # parent url
    parent_url = None
    # TRIAL
    parent_model = None
    related_column_to_parent = None
    # parameter for child view
    param_view_child: dict = {}

    def __init__(self, *args: t.Any, **kwargs):
        ViewMixin.__init__(self, *args, **kwargs)

    def get(self, model, main_id=None) -> list:

        if main_id:
            query = model.get_by_id(model, main_id)
            payload = json.dumps(model.row_dict(model, row=query))

        else:
            query = model.query.all()
            payload = json.dumps(model.list_dict(model, data=query))

        logger.debug(f"RegisterCrud get : {self.__class__.__name__}")

        return json.loads(payload), 200

    def get_data(self, model, api_schema=None, to_dict=None):

        model = model
        data = None

        try:
            if self.order_column:
                order_column = self.order_column
            else:
                order_column = "created_at"

            if self.order_type:
                if self.order_type == "desc":
                    if self.sort_by_user:
                        data = model.query.filter_by(
                            created_by_id=current_user.id
                        ).order_by(model.__getattribute__(model, order_column).desc())
                        logger.info(f"Load data - DB - DESC - Order: {order_column}")
                    else:
                        data = model.query.order_by(
                            model.__getattribute__(model, order_column).desc()
                        )
                        logger.info(f"Load data - DB - DESC - Order: {order_column}")
                elif self.sort_by_user:
                    data = model.query.filter_by(
                        created_by_id=current_user.id
                    ).order_by(model.__getattribute__(model, order_column).asc())
                    logger.info(f"Load data - DB - ASC - Order: {order_column}")
                else:
                    data = model.query.order_by(
                        model.__getattribute__(model, order_column).asc()
                    )
                    logger.info(f"Load data - DB - ASC - Order: {order_column}")

            elif self.sort_by_user:
                order_column = "id"
                data = model.query.filter_by(created_by_id=current_user.id).order_by(model.id)
                logger.info(f"Load data - DB - ASC - Order: {order_column}")

            else:
                order_column = "id"
                data = model.query.order_by(model.id)
                logger.info(f"Load data - DB - ASC - Order: {order_column}")

            if current_app.config["LOAD_DATA_AS_DICT"]:
                data = json.dumps(model.list_dict(model, data=data))
                return json.loads(data)
            else:
                return data

        except SQLAlchemyError as ex:
            flash(str(ex), "warning")

    def register_routes(self, *args, **kwargs):
        return

    def param_register_child_from_parent(self, model) -> list:
        # TODO: Must evaluate -> format all paramater needed in one variable as container?

        param = []

        if self.have_child:

            for column in self.link_columns:
                title = f"{model.__name__}, {ut.capitalize_words(column)}"
                backref = f"{column}"
                child_view_name = ".%s_%s" % (self.endpoint, column)
                alias = f"{ut.capitalize_words(column)}"

                param.append(
                    dict(
                        {
                            "title": title,
                            "backref": backref,
                            "child_view_name": child_view_name,
                            "alias": alias,
                            "form_name": [],
                            "columns": [],
                        }
                    )
                )

            for k in param:

                for forms in self.child_forms:

                    if str.lower(k["backref"]) in str.lower(forms.__name__):
                        k["form_name"].append(forms.__name__)

                        for f in forms():
                            if f.type not in ["HiddenField", "CSRFTokenField"]:
                                k["columns"].append(
                                    {
                                        "name": f.name.replace("_id", ""),
                                        "alias": f.label,
                                    }
                                )
        return param

    def get_parameter_from_form(self, form) -> dict:
        # TODO: Must evaluate -> explicitly define column as alternative?

        field_names = []
        field_labels = []

        for field in form:
            if field.type not in ["HiddenField", "CSRFTokenField"]:
                field_names.extend([str(field.name).replace("_id", "")])
                field_labels.extend([field.label])

        return {"field_names": field_names, "field_labels": field_labels}

    def render_crud(self, template="", *args, **kwargs):
        return self.render(
            template=template,
            param_view=self.param_view,
            param_view_api=self.make_api_endpoint(),
            *args,
            **kwargs,
        )

    def dispatch_request(self, *args: t.Any, **kwargs: t.Any):
        pass


class ListView(CrudView):
    methods = ["GET", "POST"]
    decorators = []

    def __init__(self, app="", *args, **kwargs):
        CrudView.__init__(self, app=app, *args, **kwargs)

    @staticmethod
    def set_search_columns(search_columns_data, extra_collection=None):
        if extra_collection:
            param = [extra_collection]

        else:
            param = [("", "")]

        for column in search_columns_data:

            if "_id" not in column["column"]:

                param.append(
                    (
                        column["column"],
                        column["column"].replace("_", " ").title(),
                    )
                )

            else:

                param.append(
                    (
                        column["column"].replace("_id", ""),
                        column["column"].replace("_id", "").replace("_", " ").title(),
                    )
                )

        return param

    def get_search_columns(self, model, extra_collection=None):
        search_columns = self.set_search_columns(
            search_columns_data=model.format_search_column(model),
            extra_collection=("", "---Column---"),
        )

        return search_columns

    def search_form(self, form, model):
        search_columns = self.get_search_columns(model)
        return form(searchable_column_choices=search_columns)

    def search(self, search_form, model, data):
        param_column = search_form.columns.data
        param_string = str(search_form.param_string.data)

        if param_column is not None and param_column != "":

            col = model.get_searchable_column(model, param_column)

            if col["model_ref"] is None:
                data = model.get_filter(model, column=param_column, value=param_string)

            elif "self_column_relation" in col:
                data = model.get_filter_with_many_to_many(
                    model,
                    model_ref=col["model_ref"],
                    self_column_relation=col["self_column_relation"],
                    column_ref=col["column_ref"],
                    value=param_string,
                )

            else:
                data = model.get_filter_with_relation(
                    model,
                    model_ref=col["model_ref"],
                    column_ref=col["column_ref"],
                    value=param_string,
                )

        return data

    def register_routes(self, *args, **kwargs):
        logger.debug("register-routes List View")
        view = ListView.as_view(
            name=self.param_view["list_view_name"],
            *args,
            **kwargs,
        )

        if self.child:
            self.app.add_url_rule(f"{self.parent_url}{self.url}/", view_func=view)
        else:
            self.app.add_url_rule(f"{self.url}/", view_func=view)

    def dispatch_request(self, main_id="", child_id="", *args, **kwargs):
        param_view_api = self.param_view_api
        api_endpoint = url_for(
            f"{self.app.name}.{param_view_api['api_list_view_name']}"
        )

        endpoint = f'.{self.param_view["list_view_name"]}'
        model = self.model
        logger.debug(f"model = {self.model}")
        action = url_for(endpoint)
        data = self.get_data(model)

        search_form = self.search_form(DataSearchForm, model)

        if request.method == "POST":
            data = self.search(search_form, model, data)

        if self.have_pagination:
            param_per_page = int(search_form.per_page.data)
            page = request.args.get("page", default=1, type=int)
            pagination = data.paginate(page=page, per_page=param_per_page)
            data = pagination.items

            return self.render_crud(
                self.list_template,
                data_list=data,
                pagination=pagination,
                child=self.child,
                data_search_form=search_form,
                action=action,
                related_column_to_parent=self.related_column_to_parent,
                *args,
                **kwargs,
            )

        else:

            return self.render_crud(
                self.list_template,
                data_list=data,
                api_endpoint=api_endpoint,
                data_search_form=search_form,
                action=action,
                view_columns=self.view_columns,
                child=self.child,
                related_column_to_parent=self.related_column_to_parent,
                *args,
                **kwargs,
            )


class AddView(CrudView):
    methods = ["GET", "POST"]
    decorators = []

    def __init__(self, app="", *args, **kwargs):
        CrudView.__init__(self, app=app, *args, **kwargs)

    def register_routes(self, *args, **kwargs):

        add_view = AddView.as_view(
            name=self.param_view["add_view_name"],
            *args,
            **kwargs,
        )

        if self.child:
            self.app.add_url_rule(
                "%s/<main_id>%s/add/" % (self.parent_url, self.url),
                view_func=add_view,
            )
            self.app.add_url_rule(
                "%s%s/add/" % (self.parent_url, self.url),
                view_func=add_view,
            )
        else:
            self.app.add_url_rule(f"{self.url}/add/", view_func=add_view)

    def dispatch_request(
        self, main_id="", child_as_main_list="", redirect_if_success="", **kwargs
    ):

        if main_id:
            parent_model = self.parent_model
            data = parent_model.query.get_or_404(main_id)
            form = self.form()
            action = url_for(".%s" % self.param_view["add_view_name"], main_id=main_id)

        else:
            data = self.model()
            form = self.form(obj=data)
            action = url_for(".%s" % self.param_view["add_view_name"])

        if form.validate_on_submit():
            try:
                if main_id and self.media:
                    upload_image_file(
                        after_endpoint=url_for(
                            ".%s%s" % (self.parent_endpoint, "_edit"), main_id=main_id
                        ),
                        form=self.form(),
                        main_model=self.parent_model(),
                        child_model=self.model(),
                        main_id=main_id,
                    )

                elif main_id:
                    form.populate_obj(data)
                    data.add_parent_id(main_id)
                    data.created_by_id = current_user.id
                    db.session.add(data)

                else:
                    form.populate_obj(data)
                    logger.debug(f"form data: {dict(form.data)}")
                    data.on_add()
                    data.created_by_id = current_user.id
                    db.session.add(data)

                db.session.commit()

                flash("You have successfully added a new data.", "success")

                if main_id:
                    return redirect(
                        url_for(
                            ".%s%s" % (self.parent_endpoint, "_edit"), main_id=main_id
                        )
                    )
                else:
                    if redirect_if_success:
                        return redirect(redirect_if_success)
                    else:
                        return redirect(
                            url_for(".%s" % self.param_view["list_view_name"])
                        )

            except SQLAlchemyError as ex:
                db.session.rollback()
                flash(str(ex), "warning")

                if main_id:
                    return redirect(
                        url_for(
                            ".%s" % self.param_view_child["add_view_name"],
                            main_id=main_id,
                        )
                    )

        if main_id:

            return self.render_crud(
                self.form_template,
                form=form,
                action=action,
                main_data=data,
                main_id=main_id,
            )

        else:

            return self.render_crud(self.form_template, form=form, action=action)


class EditView(CrudView):
    """This edit class is also used to load child data list view when parent edit form opened"""

    methods = ["GET", "POST"]
    decorators = []

    def __init__(self, app="", *args, **kwargs):
        CrudView.__init__(self, app=app, *args, **kwargs)

    def register_routes(self, *args, **kwargs):

        edit_view = EditView.as_view(
            name=self.param_view["edit_view_name"],
            *args,
            **kwargs,
        )

        if self.child:

            self.app.add_url_rule(
                "%s/<main_id>%s/<child_id>/" % (self.parent_url, self.url),
                view_func=edit_view,
            )

            self.app.add_url_rule(
                "%s%s/<child_id>/" % (self.parent_url, self.url),
                view_func=edit_view,
            )

        else:
            self.app.add_url_rule("%s/<main_id>/" % self.url, view_func=edit_view)

    def dispatch_request(
        self, main_id="", have_media="", child_id="", child_as_main_list="", **kwargs
    ):

        edit_endpoint = f'.{self.param_view["edit_view_name"]}'

        model = self.model

        if child_id:

            data = model.query.get_or_404(child_id)
            action = url_for(edit_endpoint, main_id=main_id, child_id=child_id)

        else:

            data = model.query.get_or_404(main_id)
            action = url_for(edit_endpoint, main_id=main_id)

        form = self.form(obj=data)

        logger.debug(f"form data: {dict(form.data)}")
        if form.validate_on_submit():
            try:
                form.populate_obj(data)
                db.session.commit()

                flash("You have successfully edit data.", "success")

            except SQLAlchemyError as ex:
                db.session.rollback()
                flash(str(ex), "warning")
                logger.error(f"SQLAlchemy error: {ex}")

            if child_id:
                if child_as_main_list:
                    return redirect(
                        url_for(
                            ".%s" % self.param_view_child["list_view_name"],
                            child_as_main_list=child_as_main_list,
                        )
                    )
                else:
                    return redirect(
                        url_for(
                            ".%s%s" % (self.parent_endpoint, "_edit"), main_id=main_id
                        )
                    )

            else:
                return redirect(url_for(".%s" % self.param_view["list_view_name"]))

        if self.have_child:

            param_view_child = self.param_register_child_from_parent(model)

            return self.render_crud(
                self.form_template,
                form=form,
                action=action,
                data_list=data,
                main_id=main_id,
                have_child=self.have_child,
                param_view_child=param_view_child,
                list_detail_template=self.list_detail_template,
                child=self.child,
                **kwargs,
            )

        else:

            return self.render_crud(
                self.form_template,
                form=form,
                action=action,
                data_list=data,
                main_id=main_id,
                param_fields=self.view_columns,
                child=self.child,
                child_id=child_id,
                **kwargs,
            )


class DeleteView(CrudView):
    methods = ["GET", "POST"]
    decorators = []

    def __init__(self, app="", *args, **kwargs):
        CrudView.__init__(self, app=app, *args, **kwargs)

    def register_routes(self, *args, **kwargs):

        delete_view = DeleteView.as_view(
            name=self.param_view["delete_view_name"],
            **kwargs,
        )

        if self.child:
            self.app.add_url_rule(
                "%s/<main_id>%s/<int:child_id>/delete/" % (self.parent_url, self.url),
                view_func=delete_view,
            )

            self.app.add_url_rule(
                "%s%s/<int:child_id>/delete/" % (self.parent_url, self.url),
                view_func=delete_view,
            )

        else:

            self.app.add_url_rule(
                f"{self.url}/<main_id>/delete/", view_func=delete_view
            )

    def dispatch_request(
        self,
        main_id="",
        child_id="",
        child_as_main_list="",
        redirect_if_success="",
        *args,
        **kwargs,
    ):

        if child_id:
            data = self.model.query.get_or_404(child_id)
        else:
            data = self.model.query.get_or_404(main_id)

        try:
            db.session.delete(data)
            db.session.commit()
            flash("You have successfully delete data.", "warning")
        except SQLAlchemyError as ex:
            db.session.rollback()
            flash(str(ex), "warning")

        if child_id:

            logger.debug(f"parent_endpoint = {self.parent_endpoint}")

            if child_as_main_list:
                return redirect(
                    url_for(
                        ".%s" % self.param_view_child["list_view_name"],
                        child_as_main_list=child_as_main_list,
                    )
                )
            else:
                return redirect(
                    url_for(".%s%s" % (self.parent_endpoint, "_edit"), main_id=main_id)
                )

        else:

            if redirect_if_success:
                return redirect(redirect_if_success)
            else:
                return redirect(url_for(f".{self.param_view['list_view_name']}"))


class CrudManager(CrudView):

    list_decorators = None
    edit_decorators = None
    delete_decorators = None
    add_decorators = None
    view_decorators = None

    def __init__(self, *args, **kwargs):
        CrudView.__init__(self, *args, **kwargs)

    def register_routes(self, *args, **kwargs):
        ListView.register_routes(self, *args, **kwargs)
        AddView.register_routes(self, *args, **kwargs)
        EditView.register_routes(self, *args, **kwargs)
        DeleteView.register_routes(self, *args, **kwargs)


class APIManager(RoutesMixin, MethodView):
    """[summary]
    Since we just need route for api, we inherite from route mixin.
    And we use method view for request.
    """

    child = None

    def __init__(self, *args, **kwargs):
        RoutesMixin.__init__(self, *args, **kwargs)

    # TODO: register_view: Masih harus di evaluasi dan diperbaiki
    def register_routes(self, *args, **kwargs):

        view = APIManager.as_view(
            name=self.param_view_api["api_list_view_name"],
            *args,
            **kwargs,
        )

        if self.child:

            self.app.add_url_rule(
                f"/api{self.parent_url}{self.url}/",
                view_func=view,
            )

            self.app.add_url_rule(
                f"/api{self.parent_url}{self.url}/<child_id>/",
                view_func=view,
            )

            self.app.add_url_rule(
                f"/api{self.parent_url}/<main_id>{self.url}/",
                view_func=view,
            )

            self.app.add_url_rule(
                f"/api{self.parent_url}/<main_id>{self.url}/<child_id>/",
                view_func=view,
            )

        else:

            self.app.add_url_rule(f"/api{self.url}/", view_func=view)
            self.app.add_url_rule(f"/api{self.url}/<main_id>/", view_func=view)

    def get(self, main_id=None, child_id=None, column=None, *args, **kwargs):

        payload = None

        if self.child:

            parent_model = self.parent_model
            logger.debug(f"parent_model == {parent_model}")
            logger.debug(f"model == {self.model}")

            if not main_id and not child_id:
                model = self.model
                query = model.query.all()
                payload = json.dumps(model.list_dict(model, data=query))

            elif child_id and not main_id:
                model = self.model
                query = model.query.get_or_404(child_id)
                payload = json.dumps(model.row_dict(model, row=query))

            elif child_id and main_id:
                model = self.model
                query = model.query.get_or_404(child_id)
                payload = json.dumps(model.row_dict(model, row=query))

            elif main_id and not child_id:
                model = self.model
                query = model.get_child_list(
                    model,
                    main_model=self.parent_model,
                    main_id=main_id,
                    column=(self.url).replace("/", ""),
                )
                payload = json.dumps(model.list_dict(model, data=query))

        else:
            model = self.model

            if main_id:
                query = model.query.get_or_404(main_id)
                payload = json.dumps(model.row_dict(model, row=query))

            else:
                query = model.query.all()
                payload = json.dumps(model.list_dict(model, data=query))

        payload = jsonify(json.loads(payload)), 200

        logger.debug(f"API payload: {payload}")
        return payload

    def _model_to_dict(self, obj):
        """Serialize a model instance to dict using its table columns."""
        return {c.name: getattr(obj, c.name) for c in obj.__table__.columns}

    def post(self):

        if "api" not in request.path:
            model = self.model()
            form = self.form()

            try:
                form.populate_obj(model)
                db.session.add(model)
                db.session.commit()

            except ValidationError as err:
                return {"errors": err.messages}, 422

            return redirect(url_for(self.endpoint))

        else:
            data = request.get_json(force=True, silent=True) or {}

            logger.debug(f"API POST data: {data}")

            if not data:
                return {"message": "No input data provided"}, 400

            if self.schema:
                schema = self.schema()
                try:
                    result = schema.load(data)
                    db.session.add(result)
                    db.session.commit()
                    return make_response(jsonify(self._model_to_dict(result)), 201)
                except ValidationError as err:
                    return {"errors": err.messages}, 422
            else:
                obj = self.model()
                for col in obj.__table__.columns:
                    if col.name != "id" and col.name in data:
                        setattr(obj, col.name, data[col.name])
                try:
                    db.session.add(obj)
                    db.session.commit()
                    return make_response(jsonify(self._model_to_dict(obj)), 201)
                except SQLAlchemyError as ex:
                    db.session.rollback()
                    return {"message": str(ex)}, 500

    def put(self, id):
        if not id:
            return {"message": "ID is required"}, 400

        obj = self.model.query.get_or_404(id)
        json_data = request.get_json(force=True, silent=True) or {}

        logger.debug(f"PUT json_data: {json_data}")

        if not json_data:
            return {"message": "No input data provided"}, 400

        if self.schema:
            schema = self.schema()
            try:
                result = schema.load(json_data, instance=obj, partial=True)
                db.session.commit()
                return {"message": "Data updated.", "result": self._model_to_dict(result)}, 200
            except ValidationError as err:
                return {"errors": err.messages}, 422
            except SQLAlchemyError as ex:
                db.session.rollback()
                logger.error(f"PUT error: {ex}")
                return {"message": str(ex)}, 500
        else:
            for col in obj.__table__.columns:
                if col.name != "id" and col.name in json_data:
                    setattr(obj, col.name, json_data[col.name])
            try:
                db.session.commit()
                return {"message": "Data updated.", "result": self._model_to_dict(obj)}, 200
            except SQLAlchemyError as ex:
                db.session.rollback()
                logger.error(f"PUT error: {ex}")
                return {"message": str(ex)}, 500

    def delete(self, id):
        # delete a single data
        if not id:
            return {"message": "ID is required"}, 400

        data = self.model.query.get_or_404(id)

        try:
            db.session.delete(data)
            db.session.commit()
            return make_response(jsonify({"message": "Data deleted successfully."}), 200)
        except SQLAlchemyError as ex:
            db.session.rollback()
            logger.error(f"Delete error: {ex}")
            return {"message": str(ex)}, 500


class ViewManager(ViewMixin):
    def __init__(self, *args: t.Any, **kwargs: t.Any):

        logger.debug(f"ViewManager Init : {self.app}")
        logger.debug(f"CRUD = {self.crud}")

        ViewMixin.__init__(self, *args, **kwargs)

        RoutesMixin.make_endpoint(self, *args, **kwargs)
        RoutesMixin.make_api_endpoint(self, *args, **kwargs)

        CrudManager.register_routes(self, *args, **kwargs)
        APIManager.register_routes(self, *args, **kwargs)

    def register_routes(self, *args: t.Any, **kwargs: t.Any):
        return super().register_routes(*args, **kwargs)

    def dispatch_request(self, *args, **kwargs):
        return super().dispatch_request(*args, **kwargs)

    def render(self, template="", *args: t.Any, **kwargs: t.Any):
        return super().render(template, *args, **kwargs)


class MenuRegistry(ViewMixin):
    """
    - setup global menu
    """

    gmenu = []
    menu = []
    menu_collect = []

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.make_gmenu()

    def make_menu(self, *args, **kwargs):
        self.menu.append(
            {
                # "main_title": self.main_title,
                # "title": self.title,
                # "url": "{}/".format(self.url),
                # "endpoint": "{}_home".format(self.endpoint),
            },
        )
        return

    def make_gmenu(self, *args, **kwargs):
        for menu in self.param_menu:
            if menu not in self.gmenu:
                self.gmenu.append(menu)
        return self.gmenu