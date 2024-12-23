from flask import Flask, render_template, request, jsonify, session
import sqlite3
import random
from fuzzywuzzy import fuzz

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # يجب تعيين مفتاح سري لجلسات Flask

# --- قاعدة بيانات التعليقات ---
def init_db():
    conn = sqlite3.connect('chat.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS comments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            content TEXT NOT NULL,
            parent_id INTEGER DEFAULT NULL,
            user TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

init_db()

def get_comments():
    conn = sqlite3.connect('chat.db')
    cursor = conn.cursor()
    cursor.execute('SELECT id, content, parent_id, user, timestamp FROM comments ORDER BY parent_id ASC, timestamp DESC')
    comments = cursor.fetchall()
    conn.close()
    return [{'id': comment[0], 'content': comment[1], 'parent_id': comment[2], 'user': comment[3], 'timestamp': comment[4]} for comment in comments]

def add_comment(content, user, parent_id=None):
    conn = sqlite3.connect('chat.db')
    cursor = conn.cursor()
    cursor.execute('INSERT INTO comments (content, parent_id, user) VALUES (?, ?, ?)', (content, parent_id, user))
    conn.commit()
    conn.close()

# --- قائمة الأسئلة مع الخيارات ---
questions_pool = [
    {'question': 'ما هي المقاربة الوظيفية؟', 
     'choices': ['تحليل مكونات النظام', 'تركيز على الوظائف المطلوبة', 'إجراء دراسة تقنية', 'تحليل الجدوى الاقتصادية'], 
     'answer': 'تركيز على الوظائف المطلوبة'},
     
    {'question': 'ما الفرق بين المقاربة الوظيفية والمقاربة التقنية؟', 
     'choices': ['الوظيفية تركز على المكونات', 'التقنية تركز على الوظائف', 'الوظيفية تركز على الأهداف', 'لا فرق بينهما'], 
     'answer': 'الوظيفية تركز على الأهداف'},
     
    {'question': 'ما هي الفائدة الرئيسية من المقاربة الوظيفية؟', 
     'choices': ['تقليل التكاليف فقط', 'تحقيق الأهداف بكفاءة', 'زيادة عدد المكونات', 'إلغاء الحاجة للتقنية'], 
     'answer': 'تحقيق الأهداف بكفاءة'},
     
    {'question': 'في أي المجالات تُستخدم المقاربة الوظيفية؟', 
     'choices': ['التصميم الهندسي فقط', 'الأنظمة الذكية فقط', 'الأنظمة الإلكترونية والميكانيكية', 'المجالات الاقتصادية فقط'], 
     'answer': 'الأنظمة الإلكترونية والميكانيكية'},
     
    {'question': 'كيف تساهم المقاربة الوظيفية في تحسين الأنظمة الآلية؟', 
     'choices': ['بزيادة التعقيد', 'بتحديد الوظائف الأساسية', 'بتقليل الوظائف', 'باستخدام المكونات الرخيصة فقط'], 
     'answer': 'بتحديد الوظائف الأساسية'},
     
    {'question': 'ما هي الخطوة الأولى في المقاربة الوظيفية؟', 
     'choices': ['اختبار الأداء', 'تحديد الوظائف المطلوبة', 'تصميم النظام', 'تحديد المكونات التقنية'], 
     'answer': 'تحديد الوظائف المطلوبة'},
     
    {'question': 'لماذا تُعتبر الدوال المنطقية أساسية في الأنظمة الوظيفية؟', 
     'choices': ['لأنها تُسهل اتخاذ القرارات', 'لأنها تقلل عدد المكونات', 'لأنها تزيد التعقيد', 'لأنها تحذف البيانات'], 
     'answer': 'لأنها تُسهل اتخاذ القرارات'},
     
    {'question': 'أي من هذه الدوال يُستخدم للتحقق من شرطين معًا؟', 
     'choices': ['OR', 'NOT', 'AND', 'XOR'], 
     'answer': 'AND'},
     
    {'question': 'ما هي دالة NOT؟', 
     'choices': ['تُعطي العكس للمدخلات', 'تتحقق من شرطين', 'تُظهر أحد الخيارات فقط', 'تجمع بين المدخلات'], 
     'answer': 'تُعطي العكس للمدخلات'},
     
    {'question': 'كيف تُساعد المقاربة الوظيفية في تقليل التكاليف؟', 
     'choices': ['عن طريق إلغاء الوظائف', 'بتحليل الوظائف الأساسية', 'باستخدام مواد رخيصة فقط', 'بعدم التركيز على الأهداف'], 
     'answer': 'بتحليل الوظائف الأساسية'}
]

# --- الصفحات ---

@app.route('/')
def index():
    return render_template('home.html')

@app.route('/lessons')
def lessons():
    lessons_content = [
        {'title': 'المقاربة الوظيفية', 'content': 'تعتبر المقاربة الوظيفية من الأساليب الهامة في تحليل وتصميم الأنظمة المعقدة...'},
        {'title': 'الدوال المنطقية', 'content': 'الدوال المنطقية تُستخدم في الأنظمة الوظيفية لضبط شروط اتخاذ القرارات...'}
    ]
    return render_template('lessons.html', lessons=lessons_content)

@app.route('/chat')
def chat():
    comments_list = get_comments()
    return render_template('chat.html', comments=comments_list)

@app.route('/exam', methods=['GET', 'POST'])
def exam():
    if request.method == 'POST':
        # استرجاع إجابات المستخدم
        user_answers = request.form
        score = 0

        # مقارنة إجابات المستخدم مع الإجابات الصحيحة
        for i, question in enumerate(questions_pool[:10], start=1):
            if user_answers.get(f'q{i}') == question['answer']:
                score += 1

        # تحديد حالة النجاح أو الرسوب
        passed = score >= 6  # النجاح يتطلب على الأقل 6 إجابات صحيحة

        # إعادة عرض الصفحة مع النتيجة
        return render_template('exam.html', questions=questions_pool[:10], score=score, passed=passed, user_answers=user_answers)

    # الطلب GET: عرض 10 أسئلة عشوائية
    random_questions = random.sample(questions_pool, min(10, len(questions_pool)))
    return render_template('exam.html', questions=random_questions, passed=None, user_answers=None)


# إضافة تعليق
@app.route('/add_comment', methods=['POST'])
def add_comment_endpoint():
    content = request.form['content']
    user = request.form['user']
    parent_id = request.form.get('parent_id')
    add_comment(content, user, parent_id)
    return jsonify({'status': 'success'})
 # العودة إلى صفحة الدردشة بعد إضافة التعليق

@app.route('/get_comments', methods=['GET'])
def get_comments_endpoint():
    comments_list = get_comments()  # استرجاع التعليقات من قاعدة البيانات
    return jsonify(comments_list)  # إرجاع التعليقات بصيغة JSON

if __name__ == '__main__':
    app.run(debug=True)

