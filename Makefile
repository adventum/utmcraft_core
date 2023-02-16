dev-env:
	docker-compose -f dev/docker-compose.yaml up -d
	. venv/bin/activate
	pip install --upgrade pip
	pip install --upgrade -r requirements.txt
	pip install --upgrade -r dev/requirements_dev.txt
	python utmcraft/manage.py migrate
	python utmcraft/manage.py init_user --password 12345
	make load-fixtures

stop-dev-env:
	docker-compose -f dev/docker-compose.yaml stop

run-dev:
	python utmcraft/manage.py runserver

dump-fixtures:
	python utmcraft/manage.py dumpdata --format=yaml core.Field > utmcraft/core/fixtures/fields.yaml
	python utmcraft/manage.py dumpdata --format=yaml core.FormField > utmcraft/core/fixtures/form_fields.yaml
	python utmcraft/manage.py dumpdata --format=yaml core.InputTextFormField > utmcraft/core/fixtures/input_text_fields.yaml
	python utmcraft/manage.py dumpdata --format=yaml core.InputIntFormField > utmcraft/core/fixtures/input_int_fields.yaml
	python utmcraft/manage.py dumpdata --format=yaml core.CheckboxFormField > utmcraft/core/fixtures/checkbox_fields.yaml
	python utmcraft/manage.py dumpdata --format=yaml core.RadiobuttonFormField > utmcraft/core/fixtures/radio_button_fields.yaml
	python utmcraft/manage.py dumpdata --format=yaml core.SelectFormField > utmcraft/core/fixtures/select_fields.yaml
	python utmcraft/manage.py dumpdata --format=yaml core.SelectFormFieldDependence > utmcraft/core/fixtures/select_dependences.yaml
	python utmcraft/manage.py dumpdata --format=yaml core.ResultField > utmcraft/core/fixtures/result_fields.yaml
	python utmcraft/manage.py dumpdata --format=yaml core.CombinedField > utmcraft/core/fixtures/combined_fields.yaml
	python utmcraft/manage.py dumpdata --format=yaml core.LookupTableField > utmcraft/core/fixtures/lookup_fields.yaml
	python utmcraft/manage.py dumpdata --format=yaml core.Form > utmcraft/core/fixtures/forms.yaml
	python utmcraft/manage.py dumpdata --format=yaml authorization.Profile > utmcraft/authorization/fixtures/profiles.yaml
	python utmcraft/manage.py dumpdata --format=yaml client_admin.ClientAdmin > utmcraft/client_admin/fixtures/client_admin.yaml

load-fixtures:
	python utmcraft/manage.py loaddata utmcraft/core/fixtures/fields.yaml
	python utmcraft/manage.py loaddata utmcraft/core/fixtures/form_fields.yaml
	python utmcraft/manage.py loaddata utmcraft/core/fixtures/input_text_fields.yaml
	python utmcraft/manage.py loaddata utmcraft/core/fixtures/input_int_fields.yaml
	python utmcraft/manage.py loaddata utmcraft/core/fixtures/checkbox_fields.yaml
	python utmcraft/manage.py loaddata utmcraft/core/fixtures/radio_button_fields.yaml
	python utmcraft/manage.py loaddata utmcraft/core/fixtures/select_fields.yaml
	python utmcraft/manage.py loaddata utmcraft/core/fixtures/select_dependences.yaml
	python utmcraft/manage.py loaddata utmcraft/core/fixtures/result_fields.yaml
	python utmcraft/manage.py loaddata utmcraft/core/fixtures/combined_fields.yaml
	python utmcraft/manage.py loaddata utmcraft/core/fixtures/lookup_fields.yaml
	python utmcraft/manage.py loaddata utmcraft/core/fixtures/forms.yaml
	python utmcraft/manage.py loaddata utmcraft/authorization/fixtures/profiles.yaml
	python utmcraft/manage.py loaddata utmcraft/client_admin/fixtures/client_admin.yaml

freeze:
	python -m pip freeze > requirements_prod.txt

black:
	black . --target-version py311 --preview
