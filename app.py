from flask import Flask,request,redirect,url_for,render_template,flash,session,send_file
from otp import genotp
from cmail import sendmail
from token_1 import encode,decode
import mysql.connector
from io import BytesIO
from flask_session import Session
import flask_excel as excel
import re
# mydb=mysql.connector.connect(host='localhost',user='root',password='admin',db='snmprg')
from mysql.connector import (connection)
mydb= connection.MySQLConnection(user='root', password='admin',host='localhost',database='snmprg')
app=Flask(__name__)
excel.init_excel(app)
app.config['SESSION_TYPE']="filesystem"
Session(app)
app.secret_key='codegnan@2018'
@app.route('/')
def home():
    return render_template('welcome.html')
@app.route('/create',methods=['GET','POST'])
def create():
    if request.method=='POST':
        print(request.form)
        uname=request.form['username']
        uemail=request.form['email']
        password=request.form['psd']
        cpassword=request.form['cpsd']
        cursor=mydb.cursor(buffered=True)
        cursor.execute('select count(*) from users where useremail=%s',[uemail])
        var1=cursor.fetchone()# only first record will give #fetchall(table lo all record)-> list of tuples #fetchmany -> 
        print(var1)
        if var1[0]==0:
            gotp=genotp()
            udata={'username':uname,'useremail':uemail,'password':password,'otp':gotp}
            subject='otp for Simple Notes App'
            body=f'verify email by using the otp {gotp}'
            sendmail(to=uemail,subject=subject,body=body)
            flash('OPT has sent to your Email')
            return redirect(url_for('otp',gotp=encode(data=udata)))
        elif var1[0]>0:
            flash('Email already Existsed')
            return redirect(url_for('login'))
    return render_template('create.html')
@app.route('/otp/<gotp>',methods=['GET','POST'])
def otp(gotp):
    if request.method=='POST':
        uotp=request.form['otp']
        try:
            dotp=decode(gotp)
        except Exception as e:
            print(e)
            return 'something went wrong'
        else:
            if uotp==dotp['otp']:
                cursor=mydb.cursor(buffered=True)
                cursor.execute('insert into users (username,useremail,password) values(%s,%s,%s)',[dotp['username'],dotp['useremail'],dotp['password']])
                mydb.commit()
                cursor.close()
                return redirect(url_for('login'))
            else:
                flash('OTP wrong')
                return redirect(url_for('create'))
    return render_template('otp.html')
@app.route('/login',methods=['GET','POST'])
def login():
    if not session.get('user'):
        if request.method=='POST':
            uemail=request.form['useremail']
            password=request.form['psd']
            cursor=mydb.cursor(buffered=True)
            cursor.execute('select count(useremail) from users where useremail=%s',[uemail])
            bdata=cursor.fetchone()
            if bdata[0]==1:
                cursor.execute('select password from users where useremail=%s',[uemail])
                bpassword=cursor.fetchone()
                if password==bpassword[0].decode('utf-8'):
                    session['user']=uemail
                    print(session) 
                    return redirect(url_for('dashboard'))
                else:
                    flash('password was wrong')
                    return redirect(url_for('login'))
            else:
                flash('Email not registered pls register')
                return redirect(url_for('create'))
        return render_template('login.html')
    else:
        return redirect(url_for('dashboard'))
@app.route('/dashboard')
def dashboard():
    if session.get('user'):
        return render_template('dashboard.html')
    else:
        return redirect(url_for('login'))
@app.route('/addnotes',methods=['GET','POST'])    
def addnotes():
        if session.get('user'):
            if request.method=='POST':
                title=request.form['title']
                description=request.form['desc']
                cursor=mydb.cursor(buffered=True)
                cursor.execute('select userid from users where useremail=%s',[session.get('user')])
                uid=cursor.fetchone()
                if uid:
                    try:
                        cursor.execute('insert into notes(title,description,userid) values(%s,%s,%s)',[title,description,uid[0]])
                        mydb.commit()
                        cursor.close()
                    except Exception as e:
                        print(e)
                        flash('Duplicate title entry')
                        return redirect(url_for('dashboard'))
                    else:
                        flash('notes added sucessfully')
                        return redirect(url_for('dashboard'))
                else:
                    return 'something went wrong to fetch uid'
            return render_template('addnotes.html')
        else:
            return redirect(url_for('login'))
        
@app.route('/forgotpass')
def forgotpass():
    if session.get('user'):
        return render_template('forgotpass.html')
    else:
        return redirect(url_for('login'))
@app.route('/viewallnotes')
def viewallnotes():
        if session.get('user'):
            try:
                cursor=mydb.cursor(buffered=True)
                cursor.execute('select userid from users where useremail=%s',[session.get('user')])
                uid=cursor.fetchone()
                cursor.execute('select nid,title,created_at from notes where userid=%s',[uid[0]])
                notesdata=cursor.fetchall()
                cursor.close()
            except Exception as e:
                print(e)
                flash('No data found')
                return redirect(url_for('dashboard'))
            else:
                return render_template('viewallnotes.html',notesdata=notesdata)
        else:
            return redirect(url_for('login'))

@app.route('/readnotes/<nid>')
def readnotes(nid):
        if session.get('user'):
            try:
                cursor=mydb.cursor(buffered=True)
                cursor.execute('select * from notes where nid=%s',[nid])
                notesdata=cursor.fetchone()
            except Exception as e:
                print(e)
                flash('notes not found')
                return redirect(url_for('dashboard'))
            else:
                return render_template('readnotes.html',notesdata=notesdata)
        else:
            return redirect(url_for('login'))       
@app.route('/update/<nid>',methods=['GET','POST'])
def update(nid):
        if session.get('user'):
            cursor=mydb.cursor(buffered=True)
            cursor.execute('select * from notes where nid=%s',[nid])
            notesdata=cursor.fetchone()
            if request.method=='POST':
                title=request.form['title']
                description=request.form['desc']
                cursor.execute('update notes set title=%s , description=%s where nid=%s',[title,description,nid])
                mydb.commit()
                flash('notes updated successfully')
                return redirect(url_for('readnotes',nid=nid))
            return render_template('update.html',notesdata=notesdata)
        else:
            return redirect(url_for('login'))

@app.route('/delete/<nid>')
def delete(nid):
        if session.get('user'):

            try:
                cursor=mydb.cursor(buffered=True)
                cursor.execute('delete from notes where nid=%s',[nid])
                mydb.commit()
            except Exception as e:
                print(e)
                flash('notes not found')
                return redirect(url_for('dashboard'))
            else:
                flash('notes deleted successfully')
            return redirect(url_for('viewallnotes'))
        else:
            return redirect(url_for('login'))

@app.route('/uploadfile',methods=['GET','POST'])
def uploadfile():
        if session.get('user'):
            try:
                if request.method=="POST":
                    filedata=request.files['files']
                    fdata=filedata.read()
                    filename=filedata.filename
                    cursor=mydb.cursor(buffered=True)
                    cursor.execute('select userid from users where useremail=%s',[session.get('user')])
                    uid=cursor.fetchone()
                    cursor.execute('insert into file_data(filename,fdata,added_by)values(%s,%s,%s)',[filename,fdata,uid[0]])
                    mydb.commit()
                    cursor.close()
                    flash('file uploded successfully')
                    return redirect(url_for('dashboard'))

            except Exception as e:
                print(e)
                flash('unable to upload file')
                return redirect(url_for('dashboard'))
            else:
                return render_template('uploadfiles.html')
        else:
            return redirect(url_for('login'))            
@app.route('/allfiles')
def allfiles():
        if session.get('user'):
            try:
                cursor=mydb.cursor(buffered=True)
                cursor.execute('select userid from users where useremail=%s',[session.get('user')])
                uid=cursor.fetchone()
                cursor.execute('select fid,filename,created_at from file_data where added_by=%s',[uid[0]])
                filesdata=cursor.fetchall()
            except Exception as e:
                print(e)
                flash('no files found')
                return redirect(url_for('dashboard'))
            else:
                return render_template('viewallfiles.html',filesdata=filesdata)
        else:
            return redirect(url_for('login'))   
@app.route('/viewfile/<fid>')
def viewfile(fid):
        if session.get('user'):
            try:
                cursor=mydb.cursor(buffered=True)
                cursor.execute('select filename,fdata from file_data where fid=%s',
                [fid])
                filedata=cursor.fetchone()
                bytes_data=BytesIO(filedata[1])
                return send_file(bytes_data,download_name=filedata[0],as_attachment=False)
            except Exception as e:
                print(e)
                flash("couldn't load file")
                return redirect(url_for('dashboard'))
        else:
            return redirect(url_for('login')) 
        
@app.route('/downloadfile/<fid>')
def downloadfile(fid):
     if session.get('user'):
        try:
            cursor=mydb.cursor(buffered=True)
            cursor.execute('select filename,fdata from file_data where fid=%s',
            [fid])
            filedata=cursor.fetchone()
            bytes_data=BytesIO(filedata[1])
            return send_file(bytes_data,download_name=filedata[0],as_attachment=True)
        except Exception as e:
            print(e)
            flash("couldn't load file")
            return redirect(url_for('dashboard'))
        else:
            return redirect(url_for('login')) 

@app.route('/delete1/<fid>')
def delete1(fid):
        if session.get('user'):

            try:
                cursor=mydb.cursor(buffered=True)
                cursor.execute('delete from file_data where fid=%s',[fid])
                mydb.commit()
            except Exception as e:
                print(e)
                flash('file not found')
                return redirect(url_for('dashboard'))
            else:
                flash('files deleted successfully')
            return redirect(url_for('allfiles'))
        else:
            return redirect(url_for('login'))
@app.route('/logout')
def logout():
    if session.get('user'):
        session.pop('user')
        return redirect(url_for('login'))
    else:
        return redirect(url_for('login'))        
@app.route('/getexceldata')
def getexceldata():
    if session.get('user'):
        try:
            cursor=mydb.cursor(buffered=True)
            cursor.execute('select userid from users where useremail=%s',[session.get('user')])
            uid=cursor.fetchone()
            cursor.execute('select nid,title,created_at from notes where userid=%s',[uid[0]])
            notesdata=cursor.fetchall()
            cursor.close()
        except Exception as e:
            print(e)
            flash('No data found')
            return redirect(url_for('dashboard'))
        else:
            array_data=[list(i) for i in notesdata]
            columns=['userid','title','Description','created_at']
            array_data.insert(0,columns)
            return excel.make_response_from_array(array_data,'xlsx',filename='notesdata')
    else:
        return redirect(url_for('login'))
@app.route('/search',methods=['GET','POST'])
def search():
     if session.get('user'):
          if request.method=='POST':
               search=request.form['searcheddata']
               strg=['A-Za-z0-9']
               pattern=re.compile(f'^{strg}',re.IGNORECASE)
               if (pattern.match(search)):
                    cursor=mydb.cursor(buffered=True)
                    cursor.execute('select * from notes where nid like %s or title like %s or description like %s or created_at like %s',[search+'%',search+'%',search+'%',search+'%',])
                    sdata=cursor.fetchall()
                    cursor.close()
                    return render_template('dashboard.html',sdata=sdata)
               else:
                    flash('No data found')
                    return redirect(url_for('dashboard'))
          else:
               return render_template('dashboard.html')
     else:
          return redirect(url_for('login'))

                

app.run(use_reloader=True,debug=True)