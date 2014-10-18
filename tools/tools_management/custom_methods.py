# Copyright (c) 2013, Web Notes Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

from __future__ import unicode_literals
import frappe
from frappe.widgets.reportview import get_match_cond
from frappe.utils import add_days, cint, cstr, date_diff, rounded, flt, getdate, nowdate, \
	get_first_day, get_last_day,money_in_words, now, nowtime
from frappe import _
from frappe.model.db_query import DatabaseQuery

def get_style(doctype, txt, searchfield, start, page_len, filters):
	return frappe.db.sql("""select distinct style 
		from `tabStyle Item` where parent='%s'"""%(filters.get('item_code')))

def branch_validation(doc, method):
	br = frappe.db.sql("select name from `tabBranch` where warehouse='%s' or cost_center='%s'"%(doc.warehouse, doc.cost_center),as_list=1)
	if br:
		frappe.throw(_("Branch or Warehouse already assigned to Branch '{0}'").format(br[0][0]))

def branches_creation(doc, method):
	if frappe.db.get_value('Branches', doc.branch, 'name') != doc.branch:
		br = frappe.new_doc('Branches')
		br.branch_name = doc.branch
		br.warehouse = doc.warehouse
		br.save(ignore_permissions=True)

def sales_invoice_on_submit_methods(doc, method):
	generate_project_aginst_si(doc, method)
	update_docstatus(doc)

def update_docstatus(doc):
	frappe.db.sql("update `tabSales Invoice Item` set docstatus=1 where parent='%s'"%(doc.name))	

def generate_project_aginst_si(doc, method):
	if not frappe.db.get_value('Project', doc.name, 'name'):
		pt = frappe.new_doc('Project')
		pt.project_name = doc.name
		pt.project_start_date = now()
		pt.save(ignore_permissions=True)
		generate_task(doc, method, pt.name)		

def generate_task(doc, method, name):
	for d in doc.get('entries'):
		if d.work_order:
			process_details = frappe.db.sql("select process from `tabWO Process` where parent='%s'"%(d.work_order))
			item_code = frappe.db.get_value('Work Order', d.work_order, 'item_code')
			if process_details:
				for process in process_details:
					create_task_against_process(doc,process[0], name, item_code)

def create_task_against_process(doc,process, name, item_code):
	if not frappe.db.get_value('Task',{'name':process,'project':name},'name') and item_code:
		c = frappe.new_doc('Task')
		c.subject = process + ' For Item ' + frappe.db.get_value('Item', item_code, 'item_name')
		c.process_name = process
		c.item_name = frappe.db.get_value('Item', item_code, 'item_name')
		c.sales_order_number = doc.name
		c.save()

def delete_project_aginst_si(doc, method):
	value = frappe.db.sql("select name from `tabTask` where sales_order_number='%s'"%(doc.name))
	if value:
		for d in value:
			frappe.db.sql("delete from `tabTime Log` where task='%s'"%(d[0]))
	frappe.db.sql("delete from `tabTask` where sales_order_number='%s'"%(doc.name))
	frappe.db.sql("delete from `tabProject` where name='%s'"%(doc.name))	

def merge_tailoring_items(doc,method):
	doc.set('entries', [])
	amt = amount = 0.0
	for d in doc.get('sales_invoice_items_one'):
		e = doc.append('entries', {})
		e.barcode=d.tailoring_barcode
		e.item_code=d.tailoring_item_code
		e.item_name=d.tailoring_item_name
		e.work_order=d.tailoring_work_order
		e.description=d.tailoring_description
		e.warehouse=d.tailoring_warehouse
		e.income_account=d.tailoring_income_account
		e.cost_center=d.tailoring_cost_center
		e.batch_no=d.tailoring_batch_no
		e.item_tax_rate=d.tailoring_item_tax_rate
		e.stock_uom=d.tailoring_stock_uom 
		e.price_list_rate=d.tailoring_price_list_rate
		e.discount_percentage=d.tailoring_discount_percentage
		e.amount= d.tailoring_amount
		e.base_amount= cstr(flt(e.amount)*flt(doc.conversion_rate))
		e.base_rate=  cstr(flt(d.tailoring_rate)*flt(doc.conversion_rate))
		e.rate=d.tailoring_rate
		e.base_price_list_rate=d.tailoring_base_price_list_rate
		e.qty=d.tailoring_qty
		e.base_price_list_rate=d.tailoring_base_price_list_rate
		amt += flt(e.amount)
	amount = merge_merchandise_items(doc)
	doc.net_total_export = cstr(flt(amount) + flt(amt))
	doc.grand_total_export = cstr(flt(amount) + flt(amt) + flt(doc.other_charges_total_export))
	doc.rounded_total_export = cstr(rounded(flt(amount) + flt(amt) + flt(doc.other_charges_total_export)))
	doc.in_words_export = cstr(money_in_words(flt(amount) + flt(amt) + flt(doc.other_charges_total_export),doc.currency))
	doc.net_total = cstr(flt(doc.net_total_export) * flt(doc.conversion_rate))
	doc.grand_total = cstr(flt(doc.net_total) + flt(doc.other_charges_total))
	doc.rounded_total = cstr(rounded(flt(doc.net_total) + flt(doc.other_charges_total)))
	doc.in_words = cstr(money_in_words(flt(doc.net_total) + flt(doc.other_charges_total)))
	doc.outstanding_amount = cstr(flt(doc.net_total) + flt(doc.other_charges_total) - flt(doc.total_advance))
	return "Done"

def merge_merchandise_items(doc):
	amount = 0.0
	for d in doc.get('merchandise_item'):
		e = doc.append('entries', {})
		e.barcode=d.merchandise_barcode
		e.item_code=d.merchandise_item_code
		e.item_name=d.merchandise_item_name
		e.work_order=d.merchandise_work_order
		e.description=d.merchandise_description
		e.warehouse=d.merchandise_warehouse
		e.income_account=d.merchandise_income_account
		e.cost_center=d.merchandise_cost_center
		e.batch_no=d.merchandise_batch_no
		e.item_tax_rate=d.merchandise_item_tax_rate
		e.stock_uom=d.merchandise_stock_uom 
		e.price_list_rate=d.merchandise_price_list_rate
		e.discount_percentage=d.merchandise_discount_percentage
		e.amount= d.merchandise_amount
		e.base_amount=cstr(flt(d.merchandise_amount)*flt(doc.conversion_rate))
		e.base_rate=cstr(flt(d.merchandise_rate)*flt(doc.conversion_rate))
		e.rate=d.merchandise_rate
		e.base_price_list_rate=d.merchandise_base_price_list_rate
		e.qty=d.merchandise_qty
		e.base_price_list_rate=d.merchandise_base_price_list_rate
		amount += flt(e.amount) 
	return amount

def get_item_details(doc, item):
	for d in doc.get('sales_invoice_items_one'):
		if d.tailoring_item_code == item:
			d.tailoring_item_name = frappe.db.get_value('Item', item, 'item_name')
			d.tailoring_description = frappe.db.get_value('Item', item, 'description')
			d.tailoring_stock_uom =frappe.db.get_value('Item', item, 'stock_uom')
			d.tailoring_rate = frappe.db.get_value('Item Price',{'price_list':d.tailoring_price_list,'item_code':item},'price_list_rate')
			d.tailoring_warehouse = frappe.db.get_value('Item', item, 'default_warehouse')
	return "Done"

def get_merchandise_item_details(doc, item):
	for d in doc.get('merchandise_item'):
		if d.merchandise_item_code == item:
			d.merchandise_item_name = frappe.db.get_value('Item', item, 'item_name')
			d.merchandise_description = frappe.db.get_value('Item', item, 'description')
			d.merchandise_stock_uom =frappe.db.get_value('Item', item, 'stock_uom')
			d.merchandise_rate = frappe.db.get_value('Item Price',{'price_list':d.merchandise_price_list,'item_code':item},'price_list_rate')
			d.merchandise_warehouse = frappe.db.get_value('Item', item, 'default_warehouse')
	return "Done"

@frappe.whitelist()
def get_styles_details(item, style):
	return frappe.db.sql("""select name,  image_viewer,default_value, abbreviation,
	cost_to_customer, cost_to_tailor from `tabStyle Item`
		where parent='%s' and style='%s'"""%(item, style),as_list=1)

@frappe.whitelist()
def get_warehouse_wise_stock_balance(item, qty):
	return frappe.db.sql("""select actual_qty, warehouse from `tabStock Ledger Entry` where item_code = '%s' and actual_qty >= %s"""%(item, qty), as_list=1)

def update_work_order(doc, method):
	frappe.db.sql(""" update `tabWork Order` set sales_invoice_no = '%(sales_invoice_no)s' 
		where name in 
			(select tailor_work_order from `tabWork Order Distribution` 
				where parent = '%(sales_invoice_no)s') """%{'sales_invoice_no':doc.name})

def create_se_or_mr(doc, method):
	if doc.fabric_details:
		fabric_details = eval(doc.fabric_details)
		user_warehouse = get_user_warehouse()
		for warehouse in fabric_details:
			for item_details in fabric_details[warehouse]:
				proc_warehouse = get_actual_fabrc_warehouse(doc.name, item_details[2])
				if proc_warehouse == user_warehouse:
					frappe.errprint("proc_warehouse and user warehouse are same")
					make_stock_transfer(proc_warehouse, warehouse, item_details[0], item_details[1])
				else:
					frappe.errprint("create material_request")
					make_material_request(proc_warehouse, warehouse, item_details[0], item_details[1])

def get_actual_fabrc_warehouse(si, item):
	ret = frappe.db.sql("""select warehouse from `tabProcess Wise Warehouse Detail` 
					where parent = ( select name from `tabWork Order` 
						where sales_invoice_no = '%s' and item_code = '%s') 
					and ifnull(actual_fabric, 0) = 1"""%(si, item), as_list=1)

	return ((len(ret[0]) > 1 ) and ret[0] or ret[0][0]) if ret else None

def get_user_warehouse():
	ret = frappe.db.sql(""" select warehouse from tabBranch b, tabUser u 
		where b.name = u.branch and u.name = '%s' """%(frappe.session.user), as_list=1)

	return ((len(ret[0]) > 1 ) and ret[0] or ret[0][0]) if ret else None	

def make_stock_transfer(proc_warehouse, warehouse, fabric, qty):
	fab_details = get_fabric_details(fabric)
	
	se = frappe.new_doc('Stock Entry')
	se.naming_series =  get_series("Stock Entry")
	se.purpose_type = 'Material Out'
	se.purpose = 'Material Issue'
	se.branch = frappe.db.get_value('User', frappe.session.use, 'branch')
	se.posting_date = nowdate()
	se.posting_time = nowtime().split('.')[0]
	
	sed = se.append('mtn_details', {})
	sed.s_warehouse = warehouse
	sed.target_branch = get_branch(proc_warehouse)
	sed.item_code = fabric
	sed.item_name = fab_details.get('item_name')
	sed.description = fab_details.get('description')
	sed.qty = qty
	sed.stock_uom = fab_details.get('stock_uom')
	sed.uom = fab_details.get('stock_uom')
	sed.conversion_factor = 1
	sed.incoming_rate = 0.0
	sed.transfet_qty = qty * 1

	se.save()

def get_series(doctype):
	return frappe.get_meta(doctype).get_field("naming_series").options or ""

def get_fabric_details(fabric):
	return frappe.db.get_value('Item', fabric,['item_name', 'description', 'stock_uom'], as_dict=1)

def get_branch(proc_warehouse):
	return frappe.db.get_value('Branch', {'warehouse': proc_warehouse}, 'name')

def make_material_request(proc_warehouse, warehouse, fabric, qty):
	fab_details = get_fabric_details(fabric)
	
	mrq = frappe.new_doc('Material Request')
	mrq.naming_series =  get_series("Material Request")
	mrq.material_request_type = 'Transfer'
	# mrq.branch = frappe.db.get_value('User', frappe.session.use, 'branch')
	
	mrqd = mrq.append('indent_details', {})
	mrqd.warehouse = proc_warehouse
	mrqd.from_warehouse = warehouse
	mrqd.item_code = fabric
	mrqd.item_name = fab_details.get('item_name')
	mrqd.description = fab_details.get('description')
	mrqd.qty = qty
	mrqd.uom = fab_details.get('stock_uom')
	mrqd.schedule_date = add_days(nowdate(), 2)

	mrq.save()