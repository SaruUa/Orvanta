import csv

from django.http import HttpResponse
from django.utils import timezone


def build_csv_response(filename, headers, rows):
    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    # BOM-\u043c\u0430\u0440\u043a\u0435\u0440 \u0434\u043b\u044f \u043a\u043e\u0440\u0435\u043a\u0442\u043d\u043e\u0433\u043e \u0432\u0456\u0434\u043e\u0431\u0440\u0430\u0436\u0435\u043d\u043d\u044f \u043a\u0438\u0440\u0438\u043b\u0438\u0446\u0456 \u0432 Microsoft Excel
    response.write('\ufeff')

    writer = csv.writer(response, delimiter=';')
    writer.writerow(headers)
    writer.writerows(rows)

    return response


def format_csv_bool(value):
    return 'Так' if value else 'Ні'


def format_csv_date(value):
    if value is None:
        return ''
    return value.strftime('%Y-%m-%d')


def format_csv_time(value):
    if value is None:
        return ''
    return value.strftime('%H:%M')


def format_csv_datetime(value):
    if value is None:
        return ''
    return timezone.localtime(value).strftime('%Y-%m-%d %H:%M')
