#!/usr/bin/env python
# coding: utf-8

from helpers.pdf2html import convert_from_path
import os
import tempfile
from shutil import rmtree
from zipfile import ZipFile


def process_file(fname, dest_dir):
    ext = os.path.splitext(fname)[-1]
    file_name = '.'.join(os.path.splitext(os.path.split(fname)[-1])[:-1])
    temp_dir = tempfile.gettempdir()
    if ext.lower() == '.zip':
        yield "Unzipping file..."
        temp_unzip_dir = os.path.join(temp_dir, file_name)
        try:
            rmtree(temp_unzip_dir)
        except:
            pass
        os.mkdir(temp_unzip_dir)
        with ZipFile(fname, 'r') as zipObj:
            zipObj.extract(temp_unzip_dir)
            files = [os.path.join(temp_unzip_dir, f) for f in os.listdir(temp_unzip_dir)]
    elif ext.lower() == '.pdf':
        files = [fname]
    else:
        raise Exception(
            "Unsupported file format (%s) accepted formats are: .pdf, .zip(containing pdf files)" % ext)

    client_data = {}

    for file in files:
        yield "Converting file [%s] ..." % file
        ext = os.path.splitext(file)[-1]
        file_name = '.'.join(os.path.splitext(os.path.split(fname)[-1])[:-1])
        output_file = os.path.join(dest_dir, file_name + ".html")
        if os.path.exists(output_file):
            raise Exception("Output target (%s) already exists. Please delete or rename current file before upload.")
        if ext.lower() == ".pdf":
            convert_from_path(file,
                              single_file=True,
                              output_file=output_file,
                              complex_styles=True,
                              embed_images=True,
                              center_pages=True,
                              title_from_file_name=True)
        else:
            raise Exception("Unsupported file type (%s) please only include [.pdf, .zip] files." % ext)


def zipdir(path, ziph):
    # ziph is zipfile handle
    for root, dirs, files in os.walk(path):
        for file in files:
            ziph.write(os.path.join(root, file), file)


def create_workbook(client, data, out_file):
    workbook = xlsxwriter.Workbook(out_file)
    worksheet = workbook.add_worksheet()

    odd_format = workbook.add_format({
        'align': 'center',
        'valign': 'vcenter',
        'bg_color': '#C0C0C0',
        'border': 1,
        'border_color': '#C0C0C0'})

    even_format = workbook.add_format({
        'align': 'center',
        'valign': 'vcenter',
        'bg_color': 'white',
        'border': 1,
        'border_color': '#C0C0C0'})

    bold_format = workbook.add_format({
        'align': 'center',
        'valign': 'vcenter',
        'bold': True})

    bold_format_small = workbook.add_format({
        'align': 'center',
        'valign': 'vcenter',
        'bold': True,
        'font_size': 8})

    bold_format_left = workbook.add_format({
        'align': 'left',
        'valign': 'vcenter',
        'bold': True,
        'indent': 1})

    indented_format_left = workbook.add_format({
        'align': 'left',
        'valign': 'vcenter',
        'indent': 1})

    center_format = workbook.add_format({
        'align': 'center',
        'valign': 'vcenter'})

    s = 12
    worksheet.set_column('A:B', s)
    worksheet.set_column('C:D', s)
    worksheet.set_column('E:G', 0)
    worksheet.set_column('H:I', s)
    worksheet.set_column('J:K', s)
    worksheet.set_column('L:M', s)

    # Sheet Header

    r = 1

    fmt = workbook.add_format({
        'align': 'left',
        'valign': 'vcenter',
        'font_size': 21})
    worksheet.merge_range('A%d:H%d' % (r, r), 'RIDENT ROYALTIES, INC.', fmt)

    fmt = workbook.add_format({
        'align': 'right',
        'valign': 'vcenter',
        'font_color': '#000080',
        'font_size': 24,
        'bold': True})

    worksheet.merge_range('K%d:M%d' % (r, r), 'Statement', fmt)

    worksheet.insert_image('A2', './img/logo.png', {'x_scale': 0.72, 'y_scale': 0.72})

    fmt = indented_format_left
    worksheet.write("H4", 'Date:', fmt)
    worksheet.write("H5", 'Quarter:', fmt)
    worksheet.write("H6", 'Payment Method:', fmt)

    fmt = workbook.add_format({
        'align': 'left',
        'valign': 'vcenter',
        'border': 1,
        'border_color': 'black',
        'num_format': 'd mmm yyyy'})

    worksheet.merge_range("K4:M4", '=TODAY()', fmt)
    worksheet.merge_range("K5:M5", '=CONCATENATE("Q", ROUNDUP(MONTH(K4)/3,0), " ", YEAR(K4))', fmt)
    worksheet.merge_range("K6:M6", 'EFT', fmt)

    blue_head_left = workbook.add_format({
        'align': 'left',
        'valign': 'vcenter',
        'font_color': 'white',
        'bg_color': '#000080',
        'right': 1,
        'left': 1,
        'bold': True,
        'border_color': 'white'})

    blue_head_center = workbook.add_format({
        'align': 'center',
        'valign': 'vcenter',
        'font_color': 'white',
        'bg_color': '#000080',
        'right': 1,
        'left': 1,
        'bold': True,
        'border_color': 'white'})

    blue_foot = workbook.add_format({
        'align': 'right',
        'valign': 'vcenter',
        'font_color': 'white',
        'bg_color': '#000080',
        'right': 1,
        'left': 1,
        'bold': True,
        'border_color': 'white'})

    fmt = blue_head_left
    r = 9
    worksheet.merge_range('A%d:D%d' % (r, r), 'Payee', fmt)
    worksheet.merge_range('H%d:M%d' % (r, r), 'Account Summary', fmt)
    r = 10
    worksheet.merge_range('A%d:D%d' % (r, r), client, indented_format_left)
    worksheet.merge_range('H%d:I%d' % (r, r), 'Previous Balance', indented_format_left)
    r = 11
    worksheet.write(r - 1, 7, "Credits", indented_format_left)
    worksheet.write(r - 1, 11, "$", center_format)
    r = 12
    worksheet.write(r - 1, 7, "Debits", indented_format_left)
    r = 13
    worksheet.merge_range('H%d:I%d' % (r, r), 'Total Balance Due', bold_format_left)
    worksheet.write(r - 1, 11, "$", bold_format)
    # Table Head
    r = 16

    sums = [10, 12]

    fmt = blue_head_center

    worksheet.merge_range('A%d:B%d' % (r, r), 'Source of Payment', fmt)
    worksheet.merge_range('C%d:G%d' % (r, r), 'Countries of Origin', fmt)
    worksheet.merge_range('H%d:I%d' % (r, r), 'Amount Received', fmt)
    worksheet.merge_range('J%d:K%d' % (r, r), 'Deducted By Rident', fmt)
    worksheet.merge_range('L%d:M%d' % (r, r), 'Paid to Client', fmt)

    init_i = 16
    i = init_i
    for source, origin, amount in data:
        r = i + 1
        if r % 2:
            fmt = odd_format
        else:
            fmt = even_format

        worksheet.merge_range('A%d:B%d' % (r, r), source, fmt)
        worksheet.merge_range('C%d:G%d' % (r, r), origin, fmt)

        worksheet.write(i, 7, '$', fmt)
        worksheet.write(i, 9, '$', fmt)
        worksheet.write(i, 11, '$', fmt)

        worksheet.write(i, 8, amount, fmt)
        worksheet.write_formula(i, 10, '=I%d*0.15' % r, fmt)
        worksheet.write_formula(i, 12, '=I%d-K%d' % (r, r), fmt)

        i += 1

    fmt = blue_foot
    worksheet.write_formula(i, 12, '=SUM(M%d:M%d)' % (init_i + 1, i), fmt)

    worksheet.merge_range('J%d:K%d' % (i + 1, i + 1), 'Account Current Balance', fmt)
    worksheet.write(i, 11, "$", fmt)
    worksheet.merge_range('A%d:I%d' % (i + 1, i + 1), '', fmt)

    for s in sums:
        worksheet.write_formula(s, 12, '=M%d' % (i + 1))

    fmt = bold_format_small
    r = i + 3
    worksheet.merge_range('A%d:M%d' % (r, r),
                          ' The payment has been sent via the method indicated above.  Please note, it may take up to 10 business days for bank transfers or check to arrive.',
                          fmt)

    r += 2
    worksheet.merge_range('A%d:M%d' % (r, r), '')

    r += 2
    worksheet.merge_range('A%d:M%d' % (r, r), '')

    fmt = center_format
    r += 2
    worksheet.merge_range('A%d:M%d' % (r, r),
                          'Should you have any enquiries concerning this statement, please contact Chris Kennedy at chris@ridentroyalties.com',
                          fmt)

    r += 1
    worksheet.merge_range('A%d:M%d' % (r, r),
                          'P.O. Box 18174, Austin, TX 78760', fmt)

    fmt = worksheet.default_url_format
    fmt.set_align('center')
    r += 1
    worksheet.merge_range('A%d:M%d' % (r, r),
                          'www.ridentroyalties.com', fmt)

    worksheet.set_footer("Page &P of &N")

    workbook.close()