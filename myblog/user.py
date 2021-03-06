import pymongo
from bson import ObjectId
from flask import Blueprint
from flask import flash
from flask import g
from flask import redirect
from flask import render_template
from flask import request
from flask import url_for
import json
from werkzeug.exceptions import abort
from werkzeug.utils import secure_filename
from datetime import date, datetime
import pprint
from persiantools.jdatetime import JalaliDate

from myblog.blog import login_required
from myblog.db import get_db

bp = Blueprint("user", __name__, url_prefix='/user')


# for showing a detail of user or change his/her profile details
@login_required
@bp.route("/profile/<user_id>", methods=['GET', 'POST'])
def profile(user_id):
    if request.method == 'POST':
        image = request.files.get('image')
        email = request.form.get('email')
        phone = request.form.get('phone')
        if image:
            image.save('myblog/static/media/uploads/profiles/' +
                       secure_filename(image.filename))
            get_db().user.update({'_id': ObjectId(user_id)}, {
                '$set': {'image': image.filename, 'email': email, 'phone': phone}})
        else:

            get_db().user.update({'_id': ObjectId(user_id)},
                                 {'$set': {'email': email, 'phone': phone}})
        flash('پنل کاربری شما با موفقیت ویرایش شد', 'alert-success')
        return redirect(url_for('blog.home'))

    user = get_db().user.find_one({'_id': ObjectId(user_id)})
    return render_template('edit_profile.html', user=user)


# for showing all posts of a user who is logged in
@bp.route("/posts-list/<user_id>")
def post_list(user_id):
    posts = get_db().posts.find({'user._id': ObjectId(user_id)})
    categories = get_db().categories.find()
    tags = get_db().tag.find()
    return render_template('my_posts.html', posts=list(posts), categories=list(categories), tags=list(tags))


# for create a new post
@bp.route("/create-post/", methods=['GET', 'POST'])
@login_required
def create_post():
    categories = get_db().categories.find()
    tags = get_db().tag.find()
    if request.method == 'POST':

        db = get_db()
        title = request.form.get('title')
        content = request.form.get('content')
        category = request.form.get('category')
        tags = json.loads(request.form.get('tags'))
        tags.append(request.form.get('old-tag'))
        image = request.files.get('image')
        user = g.user
        status = True

        if image:
            image.save('myblog/static/media/uploads/posts/' +
                       secure_filename(image.filename))

        post = db.posts.find_one({"title": title})

        if post is None:
            db.posts.insert_one({'user': user, 'title': title, 'content': content,
                                 'category': category,
                                 'tag': tags, 'image': image.filename,
                                 'status': status, 'like': [], 'dislike': [], 'pub_date': str(JalaliDate.today())}
                                )

            for tag in tags:
                if not db.tag.find_one({'name': tag}):
                    db.tag.insert_one({"name": tag})
            db.posts.create_index(
                [('title', 1), ('content', 1), ('user.username', 1), ('tag', 1)])
            return redirect(url_for('blog.home'))
        else:
            flash('پست با این عنوان موجوداست عنوان دیگری انتخاب کنید', 'alert-danger')
            return render_template('new_post.html', categories=list(categories), tags=list(tags))

    return render_template('new_post.html', categories=list(categories), tags=list(tags))


# for edit a post (just title,content,tags) can be change
@bp.route("/edit-post/<post_id>", methods=['POST'])
def edit_post(post_id):
    title = request.form.get('title')
    content = request.form.get('content')
    tags = json.loads(request.form.get('tags'))
    get_db().posts.update({'_id': ObjectId(post_id)}, {
        '$set': {'title': title, 'content': content, 'tag': tags}})

    return render_template('detail_post.html', post=get_db().posts.find_one({'_id': ObjectId(post_id)}))
