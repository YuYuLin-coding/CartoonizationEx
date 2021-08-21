from flask import Flask, url_for, redirect, render_template, request, make_response, flash, session
from flask_login import LoginManager, UserMixin, login_user, current_user, login_required, logout_user
from werkzeug.utils import secure_filename
import time
import datetime
import cv2
import os
from cartoonize import WB_Cartoonize
from moviepy.editor import VideoFileClip
import moviepy.editor as mpy
import sqlite3
import json

# connect to database
connect = sqlite3.connect('userinfo.db', check_same_thread=False)
cursor = connect.cursor()

app = Flask(__name__)
app.secret_key = 'Your Key'
login_manager = LoginManager(app)


class User(UserMixin):
    """  
 設置一： 只是假裝一下，所以單純的繼承一下而以 如果我們希望可以做更多判斷，
 如is_administrator也可以從這邊來加入 
 """
    pass


@login_manager.user_loader
def user_loader(userName):
    #if userName not in users:
    #return
    user = User()
    user.id = userName
    return user


def return_img_stream(img_local_path):
    """
    工具函数:
    獲取本地圖片流
    :param img_local_path:文件單張圖片的本地絕對路徑
    :return: 圖片流
    """
    img_stream = ''
    with open(img_local_path, 'rb') as img_f:
        img_stream = img_f.read()
    return img_stream


@app.route('/')
def upload_file():
    if current_user.is_active:
        #return 'Logged in as: ' + current_user.id + 'Login is_active:True'
        return render_template('00_index.html', userName=current_user.id)
    return render_template('00_index.html', userName='Guest')


@app.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == 'GET':
        if current_user.is_active:
            return render_template('00_index.html', userName=current_user.id)
        return render_template('02_login.html')
    userName = request.form['username']
    try:
        cursor.execute("SELECT UserName FROM usertable WHERE UserName = ?",
                       (userName, )).fetchone()[0]
    except:
        flash('帳號或密碼錯誤')
        return render_template('02_login.html', userName=userName)
    if cursor.execute(
            "SELECT loginfailcounts FROM usertable WHERE UserName = ?",
        (userName, )).fetchone()[0] >= 3:
        try:
            print((datetime.datetime.now() - datetime.datetime.strptime(
                cursor.execute(
                    "SELECT logintime FROM loginrecord WHERE UserName = ? ORDER by logintime DESC",
                    (userName, )).fetchone()[0],
                '%Y-%m-%d %H:%M:%S')).total_seconds() / 60)
            if (datetime.datetime.now() - datetime.datetime.strptime(
                    cursor.execute(
                        "SELECT logintime FROM loginrecord WHERE UserName = ? ORDER by logintime DESC",
                        (userName, )).fetchone()[0],
                    '%Y-%m-%d %H:%M:%S')).total_seconds() / 60 < 10:
                flash('連續錯誤超過三次，請間隔十分鐘後輸入')
                return render_template('02_login.html')
        except:
            pass
        pass
    if request.form['password'] == cursor.execute(
            "SELECT PassWord FROM usertable WHERE UserName = ?",
        (userName, )).fetchone()[0]:
        #  實作User類別
        user = User()
        #  設置id就是userName
        user.id = userName
        #  這邊，透過login_user來記錄user_id，如下了解程式碼的login_user說明。
        login_user(user)
        cursor.execute(
            "UPDATE usertable \
                           SET loginfailcounts = ? \
                           WHERE UserName = ? ", (0, userName))
        connect.commit()
        cursor.execute(
            "INSERT INTO loginrecord (username, logintime,status) VALUES (?,?,?)",
            (userName,
             datetime.datetime.strftime(datetime.datetime.now(),
                                        '%Y-%m-%d %H:%M:%S'), 'success'))
        connect.commit()
        #  登入成功，轉址
        return redirect(url_for('protected'))
    cursor.execute(
        "UPDATE usertable \
                           SET loginfailcounts = loginfailcounts + 1 \
                           WHERE UserName = ? ",
        (userName, ),
    )
    connect.commit()
    cursor.execute(
        "INSERT INTO loginrecord (username, logintime,status) VALUES (?,?,?)",
        (userName,
         datetime.datetime.strftime(datetime.datetime.now(),
                                    '%Y-%m-%d %H:%M:%S'), 'fail'),
    )
    connect.commit()
    flash('密碼錯誤')
    return render_template('02_login.html', userName=userName)


@app.route('/protected')
#@login_required
def protected():
    """  
 在login_user(user)之後，我們就可以透過current_user.id來取得用戶的相關資訊了  
 """
    #  current_user確實的取得了登錄狀態
    if current_user.is_active:
        return render_template('05_cartoonize.html', userName=current_user.id)
    return render_template('05_cartoonize.html', userName='Guest')


@app.route('/register', methods=['POST', 'GET'])
def register():
    if current_user.is_active:
        #return 'Logged in as: ' + current_user.id + 'Login is_active:True'
        return render_template('00_index.html', userName=current_user.id)
    if request.method == 'GET':
        return render_template('01_register.html', ErrMsg=None)
    userName = request.form['username']
    passWord = request.form['password']
    cellPhone = request.form['cellphone']
    mailBox = request.form['email']
    try:
        if request.form['username'] == cursor.execute(
                "SELECT UserName FROM usertable WHERE UserName = ?",
            (userName, )).fetchone()[0]:
            return render_template('01_register.html',
                                   ErrMsg='username 已被註冊',
                                   userName=userName,
                                   cellPhone=cellPhone,
                                   mailBox=mailBox)
    except:
        pass
    try:
        if request.form['cellphone'] == cursor.execute(
                "SELECT cellPhone FROM usertable WHERE CellPhone = ?",
            (cellPhone, )).fetchone()[0]:
            return render_template('01_register.html',
                                   ErrMsg='cellphone 已被註冊',
                                   userName=userName,
                                   cellPhone=cellPhone,
                                   mailBox=mailBox)
    except:
        pass
    try:
        if request.form['mail'] == cursor.execute(
                "SELECT mailBox FROM usertable WHERE MailBox = ?",
            (mailBox, )).fetchone()[0]:
            return render_template('01_register.html',
                                   ErrMsg='mailBox 已被註冊',
                                   userName=userName,
                                   cellPhone=cellPhone,
                                   mailBox=mailBox)
    except:
        pass
    cursor.execute(
        "INSERT INTO usertable (UserName, PassWord,CellPhone,MailBox) VALUES (?,?,?,?)",
        (userName, passWord, cellPhone, mailBox))
    connect.commit()
    flash('註冊成功，趕緊登入試試看吧')
    return redirect(url_for('login'))
    #return redirect(url_for('protected'))


@app.route('/member')
def membercenter():
    if current_user.is_active:
        return render_template('04_member.html', userName='current_user.id')
    return redirect(url_for('login'))


@app.route('/logout')
def logout():
    """  
 logout\_user會將所有的相關session資訊給pop掉 
 """
    logout_user()
    flash('登出成功')
    return render_template('00_index.html', userName='Guest')


@app.route('/uploader', methods=['GET', 'POST'])
def uploader():
    modelselect = request.form["modelselect"]
    model_path = modelselect + "_saved_models/"
    if request.method == 'POST':
        if request.files.get('image'):
            f = request.files['image']
            filename = secure_filename(f.filename)
            f.save(f'upload/{secure_filename(f.filename)}')
            if filename.split(".")[1] == 'gif':
                clip = VideoFileClip(f'upload/{filename}')
                clip.write_videofile(f'upload/{filename.split(".")[0]}.mp4',
                                     fps=24)
                wb_cartoonizer = WB_Cartoonize(os.path.abspath(model_path),
                                               True)
                cartoon_video_path = wb_cartoonizer.process_video(
                    f'upload/{filename.split(".")[0]}.mp4', '24/1')
                clip2 = VideoFileClip(cartoon_video_path)
                filetime = datetime.datetime.strftime(datetime.datetime.now(),
                                                      '%Y%m%d%H%M%S')
                clip2.write_gif(
                    f'static/cartoonized/{filename.split(".")[0]}{filetime}.gif'
                )
            ########call cartoonize
            else:
                img = cv2.imread(f'upload/{filename}')
                wb_cartoonizer = WB_Cartoonize(os.path.abspath(model_path),
                                               True)
                cartoonizedImg = wb_cartoonizer.infer(img)
                filetime = datetime.datetime.strftime(datetime.datetime.now(),
                                                      '%Y%m%d%H%M%S')
                cv2.imwrite(
                    f'static/cartoonized/{filename.split(".")[0]}{filetime}.jpg',
                    cartoonizedImg)
            flash('file uploaded successfully')
            messages = json.dumps(
                {"filename": f'{filename.split(".")[0]}{filetime}.jpg'})
            session['messages'] = messages
            return redirect(url_for('.display_cartoonize', messages=messages))

        if request.files.get('video'):
            f = request.files['video']
            filename = secure_filename(f.filename)
            f.save(f'upload/{filename}')

            output_frame_rate = '24/1'
            original_video_path = f'upload/{filename}'
            clip1 = VideoFileClip(original_video_path)
            audioclip1 = clip1.audio
            wb_cartoonizer = WB_Cartoonize(os.path.abspath(model_path), True)
            cartoon_video_path = wb_cartoonizer.process_video(
                original_video_path, output_frame_rate)
            clip2 = VideoFileClip(cartoon_video_path)
            new_video = clip2.set_audio(audioclip1)
            filetime = datetime.datetime.strftime(datetime.datetime.now(),
                                                  '%Y%m%d%H%M%S')
            new_video.write_videofile(
                f"static/cartoonized/{filename.split('.')[0]}{filetime}.mp4")
            flash('file uploaded successfully')
            messages = json.dumps(
                {"filename": f'{filename.split(".")[0]}{filetime}.mp4'})
            session['messages'] = messages
            return redirect(url_for('.display_cartoonize', messages=messages))


@app.route('/output')
def display_cartoonize():
    messages = request.args['messages']  # counterpart for url_for()
    messages = session['messages']  # counterpart for session
    messages = json.loads(messages)
    print(messages)
    filename = messages['filename']
    # img_path = '/Users/yq/Desktop/lessonfile/webapi/cartoonized/' + filename
    # img_stream = return_img_stream(img_path)

    if current_user.is_active:
        #return 'Logged in as: ' + current_user.id + 'Login is_active:True'
        return render_template('06_output.html',
                               userName=current_user.id,
                               filename=filename)
    return render_template('06_output.html',
                           userName='Guest',
                           filename=filename)


if __name__ == '__main__':
    app.run(debug=True)
