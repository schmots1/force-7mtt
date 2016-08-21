import os
if os.path.isfile('first_run'):
        os.system('pip install -r requirements.txt')
        os.remove('first_run')

import pandas as pd
from flask import Flask, render_template, request, redirect, url_for
import csv
import xlrd
import glob
import sqlite3 as sql
import webbrowser
from werkzeug.utils import secure_filename
import threading
url = "http://127.0.0.1:5000"
threading.Timer(2.25, lambda: webbrowser.open(url) ).start()

UPLOAD_FOLDER = './'
ALLOWED_EXTENSIONS = set(['xls', 'xlsx'])
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
def allowed_file(filename):
	return '.' in filename and filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS

@app.route('/')
def home():
   databases = glob.glob("./databases/*db")
   return render_template('home.html', databases = databases)

@app.route('/dashboard')
def dashboard():
	database = request.args.get("database")
	if not database:
		return "You need to pick a database"	
	else:
		dbname = "./databases/%s.db" % (database)
	con = sql.connect(dbname)
	con.row_factory = sql.Row
	cur = con.cursor()
	cur.execute("select count(*) from Storage_Controllers")
	result = cur.fetchone()
	controller_count = result[0]
	cur.execute("select count(*) from Vfilers where vfiler_name not in (select storage_controller from Vfilers)")
	result = cur.fetchone()
	vfiler_count = result[0]
	cur.execute("select count(*) from Aggregates")
	result = cur.fetchone()
	aggregate_count = result[0]
	cur.execute("select count(*) from Aggregates where block_type like '32-bit'")
	result = cur.fetchone()
	aggr_32_count = result[0]
	cur.execute("select count(*) from Volumes")
	result = cur.fetchone()
	volume_count = result[0]
	cur.execute("select count(*) from Volumes where block_type like '32-bit'")
	result = cur.fetchone()
	volume_32_count = result[0]
	cur.execute("select count(*) from Volumes where type like 'trad'")
	result = cur.fetchone()
	volume_trad_count = result[0]
	cur.execute("select count(*) from Qtrees")
	result = cur.fetchone()
	qtree_count = result[0]
	cur.execute("select count(*) from Luns")
	result = cur.fetchone()
	lun_count = result[0]
	cur.execute("select count(*) from CIFS_Shares where LineID is not null")
	result = cur.fetchone()
	share_count = result[0]
	cur.execute("select count(*) from NFS_Exports")
	result = cur.fetchone()
	export_count = result[0]
	cur.execute("select cast(sum(replace(total_used_size_GB,',','')) as decimal (10,2)) as total from Volumes")
	space_used = cur.fetchall()
	cur.execute("select count(*) from SnapMirror")
	result = cur.fetchone()
	snapmirror_count = result[0]
	cur.execute("select count(*) from SnapMirror where type like 'VSM'")
	result = cur.fetchone()
	vsm_count = result[0]
	cur.execute("select count(*) from SnapMirror where type like 'QSM'")
	result = cur.fetchone()
	qsm_count = result[0]
	cur.execute("select count(*) from SnapVault")
	result = cur.fetchone()
	snapvault_count = result[0]
	cur.execute("select count(*) from SnapVault where type like 'OSSV'")
	result = cur.fetchone()
	ossv_count = result[0]
	cur.execute("select count(*) from Transition_PreCheck_Summary where severity like 'Red'")
	result = cur.fetchone()
	precheck_red_count = result[0]
	cur.execute("select count(*) from Transition_PreCheck_Summary where severity like 'Yellow'")
	result = cur.fetchone()
	precheck_yellow_count = result[0]
	return render_template("dashboard.html", 
				database = database, 
				controller_count = controller_count, 
				vfiler_count = vfiler_count, 
				aggregate_count = aggregate_count, 
				aggr_32_count = aggr_32_count, 
				volume_count = volume_count,
				volume_32_count = volume_32_count, 
				volume_trad_count = volume_trad_count, 
				qtree_count = qtree_count, 
				lun_count = lun_count, 
				share_count = share_count, 
				export_count = export_count, 
				space_used = space_used, 
				snapmirror_count = snapmirror_count,
				vsm_count = vsm_count, 
				qsm_count = qsm_count, 
				snapvault_count = snapvault_count, 
				ossv_count = ossv_count, 
				precheck_red_count = precheck_red_count, 
				precheck_yellow_count = precheck_yellow_count)

@app.route('/upload', methods=['GET', 'POST'])
def uploaded_file():
    uploads = glob.glob("./*xlsx")
    if request.method == 'POST':
        # check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        # if user does not select file, browser also
        # submit a empty part without filename
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            return redirect(url_for('uploaded_file',filename=filename))

    return render_template('upload.html',uploads = uploads)

@app.route('/dbcreate', methods=['GET', 'POST'])
def dbcreate():
	excel_file = request.args.get("excel")
	dbname = request.args.get("dbname")
	if not excel_file:
		return "No file to convert."
	if not dbname:
		return render_template('createdb.html', excel_file = excel_file)
	else:
		db_name = dbname
		sql_file = './databases/%s.db' % db_name

		conn = sql.connect(sql_file)
		conn.text_factory = str
		c = conn.cursor()
	
		x1 = pd.ExcelFile(excel_file)
		sheets = x1.sheet_names

		for sheet in sheets:
			csv_file = "%s.csv" % sheet
			data_xls = pd.read_excel(excel_file, sheet, index_col=None)
			data_xls.to_csv(csv_file, encoding='utf-8')
			os.rename(csv_file, csv_file.replace(' ', '_'))
			csv_file = csv_file.replace (" ", "_")
			sheet = sheet.replace (" ", "_")
			df = pd.read_csv(csv_file)
			df.columns = pd.Series(df.columns).str.replace(' ','_')
			df.to_sql(sheet, conn, if_exists='append', index=False)
			cmd = "rm '%s'" % (csv_file)
			print sheet
			os.remove(csv_file)
		os.remove(excel_file)
		conn.commit()
		conn.close()
		return render_template('results.html')	

@app.route('/delete')
def delete():
	database  = request.args.get("database")
	confirm = request.args.get("confirm")
	if not confirm:
		return render_template('delete.html', database = database)
	dbname = "./databases/%s.db" % (database)
	os.remove(dbname)
	return redirect("http://127.0.0.1:5000")

#Begin Details Pages

@app.route('/controllers')
def controllers():
	database = request.args.get("database")
	dbname = "./databases/%s.db" % (database)
	con = sql.connect(dbname)
	con.row_factory = sql.Row

	cur = con.cursor()
	cur.execute("SELECT Storage_Controllers.*, COUNT(Aggregates.storage_controller) AS aggr FROM Storage_Controllers\
			LEFT JOIN Aggregates\
			ON Storage_Controllers.storage_controller = Aggregates.storage_controller\
			GROUP BY Storage_Controllers.storage_controller")

	rows = cur.fetchall()
	return render_template("storage_controllers.html",rows = rows,database = database)

@app.route('/vfilers')
def vfilers():
	database = request.args.get("database")
	dbname = "./databases/%s.db" % (database)
	con = sql.connect(dbname)
	con.row_factory = sql.Row

	cur = con.cursor()
	cur.execute("SELECT Vfilers.*, COUNT(Volumes.vfiler_name) AS vol,\
					COUNT(Qtrees.vfiler_name) AS qtree,\
					COUNT(Luns.vfiler_name) as lun,\
					COUNT(Cifs_Shares.vfiler_name) as share,\
					COUNT(NFS_Exports.vfiler_name) AS export,\
					COUNT(SnapMirror.vfiler_name) AS snapmirror,\
					COUNT(SnapVault.vfiler_name) as snapvault FROM Vfilers\
					LEFT JOIN Volumes\
					ON Vfilers.vfiler_name = Volumes.vfiler_name\
					LEFT JOIN Qtrees\
					ON Vfilers.vfiler_name = Qtrees.vfiler_name\
					LEFT JOIN Luns\
					ON Vfilers.vfiler_name = Luns.vfiler_name\
					LEFT JOIN Cifs_Shares\
					ON Vfilers.vfiler_name = Cifs_Shares.vfiler_name\
					LEFT JOIN NFS_Exports\
					ON Vfilers.vfiler_name = NFS_Exports.vfiler_name\
					LEFT JOIN SnapMirror\
					ON Vfilers.vfiler_name = SnapMirror.vfiler_name\
					LEFT JOIN SnapVault\
					ON Vfilers.vfiler_name = SnapVault.vfiler_name\
					Where Vfilers.vfiler_name not like Vfilers.storage_controller\
					GROUP BY Vfilers.vfiler_name")

	rows = cur.fetchall()
	return render_template("vfilers.html",rows = rows,database = database)

@app.route('/aggregates')
def aggregates():
	dbname  = request.args.get("database")
	database = request.args.get("database")
	special = request.args.get("special")
	if not special:
		dbname = "./databases/%s.db" % (dbname)
		con = sql.connect(dbname)
		con.row_factory = sql.Row
   
		cur = con.cursor()
		cur.execute("select Aggregates.*, count(Volumes.name) as vol from Aggregates\
						 left join Volumes on Aggregates.name = Volumes.aggregate_name\
						 and \
						Aggregates.storage_controller = Volumes.storage_controller\
						 group by Aggregates.Id\
						 order by storage_controller,name")
   
		rows = cur.fetchall()
	else:
		dbname = "./databases/%s.db" % (dbname)
                con = sql.connect(dbname)
                con.row_factory = sql.Row
  
                cur = con.cursor()
                cur.execute("select Aggregates.*, count(Volumes.name) as vol from Aggregates\
                                                 left join Volumes on Aggregates.name = Volumes.aggregate_name\
                                                 and \
                                                Aggregates.storage_controller = Volumes.storage_controller\
						where Aggregates.block_type like '32-bit'\
                                                 group by Aggregates.LineId\
                                                 order by storage_controller,name")

                rows = cur.fetchall()

	return render_template("aggregates.html",rows = rows, database = database)

@app.route('/volumes')
def volumes():
	dbname  = request.args.get("database")
	database = request.args.get("database")
	special = request.args.get("special")
	check = request.args.get("check")
	if not special:
		dbname = "./databases/%s.db" % (dbname)
		con = sql.connect(dbname)
		con.row_factory = sql.Row
   
		cur = con.cursor()
		cur.execute("select * from Volumes order by name,storage_controller")
   
		rows = cur.fetchall()
		return render_template("volumes.html",rows = rows, database = database)
	if special:
		dbname = "./databases/%s.db" % (dbname)
                con = sql.connect(dbname)
                con.row_factory = sql.Row

                cur = con.cursor()
		query = "select * from Volumes where %s like '%s' order by name,storage_controller" % (special, check)
                cur.execute(query)
   
                rows = cur.fetchall()
                return render_template("volumes.html",rows = rows, database = database)

@app.route('/qtrees')
def qtrees():
	database = request.args.get("database")
	dbname  = request.args.get("database")
	dbname = "./databases/%s.db" % (dbname)
	con = sql.connect(dbname)
	con.row_factory = sql.Row
   
	cur = con.cursor()
	cur.execute("select * from Qtrees order by qtree_name,storage_controller")
   
	rows = cur.fetchall()
	return render_template("qtrees.html",rows = rows, database = database)

@app.route('/luns')
def luns():
	database = request.args.get("database")
	dbname  = request.args.get("database")
	dbname = "./databases/%s.db" % (dbname)
	con = sql.connect(dbname)
	con.row_factory = sql.Row
   
	cur = con.cursor()
	cur.execute("select * from Luns order by lun_name,storage_controller")
   
	rows = cur.fetchall()
	return render_template("luns.html",rows = rows, database = database)

@app.route('/shares')
def shares():
	database = request.args.get("database")
	dbname  = request.args.get("database")
	dbname = "./databases/%s.db" % (dbname)
	con = sql.connect(dbname)
	con.row_factory = sql.Row
   
	cur = con.cursor()
	cur.execute("select * from CIFS_Shares order by share_name,storage_controller")
   
	rows = cur.fetchall()
	return render_template("shares.html",rows = rows, database = database)

@app.route('/exports')
def exports():
	database = request.args.get("database")
	dbname  = request.args.get("database")
	dbname = "./databases/%s.db" % (dbname)
	con = sql.connect(dbname)
	con.row_factory = sql.Row
   
	cur = con.cursor()
	cur.execute("select * from NFS_Exports order by storage_controller, vfiler_name, volume_name, export_path")
   
	rows = cur.fetchall()
	return render_template("exports.html",rows = rows, database = database)

@app.route('/snapmirror')
def snapmirror():
	database = request.args.get("database")
	special = request.args.get("special")
	if not special:
		dbname  = request.args.get("database")
		dbname = "./databases/%s.db" % (dbname)
		con = sql.connect(dbname)
		con.row_factory = sql.Row
   
		cur = con.cursor()
		cur.execute("select *,count(*) as count from SnapMirror group by source_controller order by storage_controller")
   
		rows = cur.fetchall()
		return render_template("snapmirror.html",rows = rows, database = database)
	if special:
		dbname  = request.args.get("database")
		dbname = "./databases/%s.db" % (dbname)
		con = sql.connect(dbname)
		con.row_factory = sql.Row
   
		cur = con.cursor()
		query = "select *,count(*) as count from SnapMirror where type like '%s' group by source_controller order by storage_controller" % special
		cur.execute(query)
   
		rows = cur.fetchall()
		return render_template("snapmirror.html",rows = rows, database = database)
		
@app.route('/snapvault')
def snapvault():
	database = request.args.get("database")
	dbname  = request.args.get("database")
	dbname = "./databases/%s.db" % (dbname)
	con = sql.connect(dbname)
	con.row_factory = sql.Row
   
	cur = con.cursor()
	cur.execute("select *,count(*) as count from SnapVault group by source_controller order by storage_controller")
   
	rows = cur.fetchall()
	return render_template("snapvault.html",rows = rows, database = database)

@app.route('/precheck')
def precheck():
	database = request.args.get("database")
	dbname  = request.args.get("database")
	dbname = "./databases/%s.db" % (dbname)
	con = sql.connect(dbname)
	con.row_factory = sql.Row
   
	cur = con.cursor()
	cur.execute("select *, count(*) as count from Transition_PreCheck_Details group by pre_check order by severity")
   
	rows = cur.fetchall()
	return render_template("precheck.html",rows = rows, database = database)

if __name__ == '__main__':
   app.run(debug = True)
