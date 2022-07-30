import operator
from re import S
from django.shortcuts import render, redirect
from django.contrib import auth
from django.contrib.auth.models import User
from django.conf import settings
from django.core.mail import send_mail
import random
from django.utils import timezone
from .models import Announcement, Assignment, Course, CourseGrade, Grade, Material, Message, Profile, SemesterLog, Submission
from rest_framework.decorators import api_view
from rest_framework.response import Response
from online_users.admin import OnlineUserActivity
from datetime import datetime, timedelta
from django.template.defaulttags import register
import csv

# Create your views here.

def home(request):
    return redirect('dashboard')

def dashboard(request):
    if request.user.is_authenticated:
        profile = Profile.objects.get(username=request.user.username)
        if profile.userType == 'Student':
            courses = Course.objects.filter(students=profile)
            student_past_semesters = SemesterLog.objects.filter(student=profile)
            actives = OnlineUserActivity.get_user_activities(timedelta(minutes=5))
            active_profiles = []
            for active in actives:
                try:
                    active_profiles.append(Profile.objects.get(username=active.user.username, userType='Student'))
                except:
                    pass
            for student_past_sememster in student_past_semesters:
                for student_past_course in student_past_sememster.courses.all(): 
                    courses = courses.exclude(code=student_past_course.code)
            assignments = Assignment.objects.filter(course__in=courses, due_date__gte=timezone.now())
            announcements = Announcement.objects.filter(course__in=courses).order_by('-id')
            courses = courses[:2]
            announcements = announcements[:3]
            return render(request, 'dashboard.html', {'profile': profile, 'courses': courses, 'assignments': assignments, 'active': active_profiles, 'announcements': announcements})
        elif profile.userType == 'Faculty':
            past_courses = Course.objects.filter(coordinators=profile)
            present_courses = Course.objects.filter(coordinators=profile)
            for course in present_courses:
                if SemesterLog.objects.filter(courses=course).exists():
                    present_courses = present_courses.exclude(code=course.code)
                else:
                    past_courses = past_courses.exclude(code=course.code)
            return render(request, 'facultyhome.html', {'profile': profile, 'present_courses': present_courses, 'past_courses': past_courses})
    return redirect('login')

def announcements(request):
    if request.user.is_authenticated:
        profile = Profile.objects.get(username=request.user.username)
        courses = Course.objects.filter(students=profile)
        student_past_semesters = SemesterLog.objects.filter(student=profile)
        for student_past_sememster in student_past_semesters:
            for student_past_course in student_past_sememster.courses.all(): 
                courses = courses.exclude(code=student_past_course.code)
        announcements = Announcement.objects.filter(course__in=courses)
        return render(request, 'announcements.html', {'profile': profile, 'announcements': announcements})
    return redirect('login')

def announcement(request, code):
    if request.user.is_authenticated:
        profile = Profile.objects.get(username=request.user.username)
        course = Course.objects.get(students=profile, code=code)
        announcements = Announcement.objects.filter(course=course)
        return render(request, 'announcement.html', {'profile': profile, 'announcements': announcements, 'course': course})
    return redirect('login')

def courses(request):
    if request.user.is_authenticated:
        profile = Profile.objects.get(username=request.user.username)
        courses = Course.objects.filter(students=profile)
        student_past_semesters = SemesterLog.objects.filter(student=profile)
        for student_past_sememster in student_past_semesters:
            for student_past_course in student_past_sememster.courses.all(): 
                courses = courses.exclude(code=student_past_course.code)
        return render(request, 'courses.html', {'profile': profile, 'courses': courses})
    return redirect('login')

def past_courses(request):
    if request.user.is_authenticated:
        profile = Profile.objects.get(username=request.user.username)
        student_past_semesters = SemesterLog.objects.filter(student=profile)
        return render(request, 'past_courses.html', {'profile': profile, 'semesters': student_past_semesters})
    return redirect('login')

def course(request, code):
    if request.user.is_authenticated:
        profile = Profile.objects.get(username=request.user.username)
        course = Course.objects.get(students=profile, code=code)
        announcements = Announcement.objects.filter(course=course).order_by('-id')
        announcements = announcements[:3]
        return render(request, 'course.html', {'profile': profile, 'course': course, 'announcements': announcements})
    return redirect('login')

def grades(request):
    if request.user.is_authenticated:
        profile = Profile.objects.get(username=request.user.username)
        student_past_semesters = SemesterLog.objects.filter(student=profile)
        grades = CourseGrade .objects.filter(student=profile)
        return render(request, 'grades.html', {'profile': profile, 'semesters': student_past_semesters, 'grades': grades})
    return redirect('login')

def course_grades(request, code):
    if request.user.is_authenticated:
        profile = Profile.objects.get(username=request.user.username)
        course = Course.objects.get(students=profile, code=code)
        assignments = Assignment.objects.filter(course=course)
        grades = Grade.objects.none()
        for assignment in assignments:
            if assignment.publish_grades:
                grades = grades.union(Grade.objects.filter(assignment=assignment, student=profile))
        if CourseGrade.objects.filter(student=profile, course=course).exists():
            fin_grade = CourseGrade.objects.get(student=profile, course=course).grade
        else:
            fin_grade = '-'
        return render(request, 'course_grades.html', {'profile': profile, 'course': course, 'grades': grades, 'fin_grade': fin_grade})
    return redirect('login')

def assignments(request):
    if request.user.is_authenticated:
        profile = Profile.objects.get(username=request.user.username)
        courses = Course.objects.filter(students=profile)
        student_past_semesters = SemesterLog.objects.filter(student=profile)
        for student_past_semester in student_past_semesters:
            for course in student_past_semester.courses.all():
                courses = courses.exclude(code=course.code)
        past_assignments = Assignment.objects.none()
        upcoming_assignments = Assignment.objects.none()
        for course in courses:
            past_assignments = past_assignments.union(Assignment.objects.filter(course=course, due_date__lt=timezone.now()))
            for past_assignment in past_assignments:
                if Submission.objects.filter(assignment=past_assignment, student=profile).exists():
                    past_assignments = past_assignments.exclude(name=past_assignment.name)
            upcoming_assignments = upcoming_assignments.union(Assignment.objects.filter(course=course, due_date__gte=timezone.now()))
            for upcoming_assignment in upcoming_assignments:
                if Submission.objects.filter(assignment=upcoming_assignment, student=profile).exists():
                    upcoming_assignments = upcoming_assignments.exclude(name=upcoming_assignment.name)
        return render(request, 'assignments.html', {'past_assignments': past_assignments, 'upcoming_assignments': upcoming_assignments, 'profile': profile})
    return redirect('login')

def course_assignments(request, code):
    if request.user.is_authenticated:
        profile = Profile.objects.get(username=request.user.username)
        course = Course.objects.get(students=profile, code=code)
        submissions = Submission.objects.filter(student=profile, course=course)
        assignments = Assignment.objects.filter(course=course)
        for assignment in assignments:
            if Submission.objects.filter(student=profile, assignment=assignment).exists():
                assignments = assignments.exclude(name=assignment.name)
        return render(request, 'course_assignments.html', {'assignments': assignments, 'profile': profile, 'course': course, 'submissions': submissions, 'assignments': assignments})
    return redirect('login')

def assignment(request, code, name):
    if request.user.is_authenticated:
        profile = Profile.objects.get(username=request.user.username)
        course = Course.objects.get(code=code, students=profile)
        assignment = Assignment.objects.get(course=course,name=name)
        if request.method == 'POST':
            submission = request.FILES['submission']
            m = submission.name.split('.')
            ext = m[len(m)-1]
            data = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789'
            name = ''.join(random.choice(data) for _ in range(300))
            submission.name = f'{name}.{ext}'
            Submission.objects.create(assignment=assignment, student=profile, submission=submission, course=course)
        if Submission.objects.filter(assignment=assignment, student=profile).exists():
            submitted = True
        else:
            submitted = False
        if assignment.due_date > timezone.now():
            late = False
        else:
            late = True
        if assignment.publish_grades:
            if Grade.objects.filter(assignment=assignment, student=profile).exists():
                marks = Grade.objects.get(assignment=assignment, student=profile).marks
            else:
                marks = 0.00
            return render(request, 'assignment.html', {'assignment': assignment, 'profile': profile, 'submitted': submitted, 'late': late, 'marks': marks})
        return render(request, 'assignment.html', {'assignment': assignment, 'profile': profile, 'submitted': submitted, 'late': late})
    return redirect('login')

def material(request, code):
    if request.user.is_authenticated:
        profile = Profile.objects.get(username=request.user.username)
        course = Course.objects.get(students=profile, code=code)
        materials = Material.objects.filter(course=course)
        return render(request, 'material.html', {'profile': profile, 'course': course, 'materials': materials})
    return redirect('login')

def participants(request, code):
    if request.user.is_authenticated:
        profile = Profile.objects.get(username=request.user.username)
        course = Course.objects.get(students=profile, code=code)
        participants = course.students.all().order_by('name')
        return render(request, 'participants.html', {'profile': profile, 'course': course, 'participants': participants})
    return redirect('login')

def manage_course(request, course):
    if request.user.is_authenticated:
        profile = Profile.objects.get(username=request.user.username)
        if profile.userType == 'Student':
            return redirect('dashboard')
        else:
            course = course.split('-')
            course = Course.objects.get(semester_code=course[0], code=course[1])
            if course.coordinators != profile:
                return redirect('dashboard')
            announcements = Announcement.objects.filter(course=course).order_by('-id')
            announcements = announcements[:3]
            return render(request, 'manage.html', {'profile': profile, 'course': course, 'announcements': announcements})
    return redirect('login')

def manage_announcements(request, course):
    if request.user.is_authenticated:
        profile = Profile.objects.get(username=request.user.username)
        if profile.userType == 'Student':
            return redirect('dashboard')
        else:
            course = course.split('-')
            course = Course.objects.get(semester_code=course[0], code=course[1])
            if course.coordinators != profile:
                return redirect('dashboard')
            announcements = Announcement.objects.filter(course=course)
            return render(request, 'manage_announcements.html', {'profile': profile, 'course': course, 'announcements': announcements})
    return redirect('login')

def add_announcement(request, course):
    if request.user.is_authenticated:
        profile = Profile.objects.get(username=request.user.username)
        if profile.userType == 'Student':
            return redirect('dashboard')
        else:
            param = course.split('-')
            course = Course.objects.get(semester_code=param[0], code=param[1])
            if course.coordinators != profile:
                return redirect('dashboard')
            if request.method == 'POST':
                Announcement.objects.create(course=course, title=request.POST['title'], description=request.POST['description'])
                return redirect(f'/manage/{param[0]}-{param[1]}/announcements')
            return render(request, 'add_announcement.html', {'profile': profile, 'course': course})
    return redirect('login')

def edit_announcement(request, course, pk):
    if request.user.is_authenticated:
        profile = Profile.objects.get(username=request.user.username)
        if profile.userType == 'Student':
            return redirect('dashboard')
        else:
            param = course.split('-')
            course = Course.objects.get(semester_code=param[0], code=param[1])
            announcement = Announcement.objects.get(id=pk)
            if course.coordinators != profile or announcement.course.coordinators != profile:
                return redirect('dashboard')
            if request.method == 'POST':
                announcement.title = request.POST['title']
                announcement.description = request.POST['description']
                announcement.save()
                return redirect(f'/manage/{param[0]}-{param[1]}/announcements')
            return render(request, 'edit_announcement.html', {'profile': profile, 'course': course, 'announcement': announcement})
    return redirect('login')

def delete_announcement(request, course, pk):
    if request.user.is_authenticated:
        profile = Profile.objects.get(username=request.user.username)
        if profile.userType == 'Student':
            return redirect('dashboard')
        else:
            param = course.split('-')
            course = Course.objects.get(semester_code=param[0], code=param[1])
            announcement = Announcement.objects.get(id=pk)
            if course.coordinators != profile or announcement.course.coordinators != profile:
                return redirect('dashboard')
            announcement.delete()
            return redirect(f'/manage/{param[0]}-{param[1]}/announcements')
    return redirect('login')

def manage_materials(request, course):
    if request.user.is_authenticated:
        profile = Profile.objects.get(username=request.user.username)
        if profile.userType == 'Student':
            return redirect('dashboard')
        else:
            course = course.split('-')
            course = Course.objects.get(semester_code=course[0], code=course[1])
            if course.coordinators != profile:
                return redirect('dashboard')
            materials = Material.objects.filter(course=course)
            return render(request, 'manage_materials.html', {'profile': profile, 'course': course, 'materials': materials})
    return redirect('login')

def add_material(request, course):
    if request.user.is_authenticated:
        profile = Profile.objects.get(username=request.user.username)
        if profile.userType == 'Student':
            return redirect('dashboard')
        else:
            param = course.split('-')
            course = Course.objects.get(semester_code=param[0], code=param[1])
            if course.coordinators != profile:
                return redirect('dashboard')
            if request.method == 'POST':
                Material.objects.create(course=course, title=request.POST['title'], material=request.FILES['material'])
                return redirect(f'/manage/{param[0]}-{param[1]}/materials')
            return render(request, 'add_material.html', {'profile': profile, 'course': course})
    return redirect('login')

def delete_material(request, course, pk):
    if request.user.is_authenticated:
        profile = Profile.objects.get(username=request.user.username)
        if profile.userType == 'Student':
            return redirect('dashboard')
        else:
            param = course.split('-')
            course = Course.objects.get(semester_code=param[0], code=param[1])
            material = Material.objects.get(id=pk)
            if course.coordinators != profile or material.course.coordinators != profile:
                return redirect('dashboard')
            material.delete()
            return redirect(f'/manage/{param[0]}-{param[1]}/materials')
    return redirect('login')

def manage_assignments(request, course):
    if request.user.is_authenticated:
        profile = Profile.objects.get(username=request.user.username)
        if profile.userType == 'Student':
            return redirect('dashboard')
        else:
            course = course.split('-')
            course = Course.objects.get(semester_code=course[0], code=course[1])
            if course.coordinators != profile:
                return redirect('dashboard')
            assignments = Assignment.objects.filter(course=course)
            return render(request, 'manage_assignments.html', {'profile': profile, 'course': course, 'assignments': assignments})
    return redirect('login')

def add_assignment(request, course):
    if request.user.is_authenticated:
        profile = Profile.objects.get(username=request.user.username)
        if profile.userType == 'Student':
            return redirect('dashboard')
        else:
            param = course.split('-')
            course = Course.objects.get(semester_code=param[0], code=param[1])
            if course.coordinators != profile:
                return redirect('dashboard')
            if request.method == 'POST':
                name = request.POST['name']
                max_marks = request.POST['max_marks']
                content = request.POST['content']
                if 'assignment' in request.FILES:
                    assignment = request.FILES['assignment']
                due_date = request.POST['due_date'] + ' ' + request.POST['due_time']
                contribution = request.POST['contribution']
                Assignment.objects.create(
                    course=course, 
                    name=name, 
                    max_marks=max_marks,
                    content=content,
                    assignment=assignment,
                    due_date=due_date,
                    contribution=contribution,
                    publish_grades=False
                )
                return redirect(f'/manage/{param[0]}-{param[1]}/assignments')
            return render(request, 'add_assignment.html', {'profile': profile, 'course': course})
    return redirect('login')

def edit_assignment(request, course, pk):
    if request.user.is_authenticated:
        profile = Profile.objects.get(username=request.user.username)
        if profile.userType == 'Student':
            return redirect('dashboard')
        else:
            param = course.split('-')
            course = Course.objects.get(semester_code=param[0], code=param[1])
            assignment = Assignment.objects.get(id=pk)
            if course.coordinators != profile or assignment.course.coordinators != profile:
                return redirect('dashboard')
            if request.method == 'POST':
                assignment.name = request.POST['name']
                assignment.max_marks = request.POST['max_marks']
                assignment.content = request.POST['content']
                if 'assignment' in request.FILES:
                    assignment.assignment = request.FILES['assignment']
                assignment.due_date = request.POST['due_date'] + ' ' + request.POST['due_time']
                assignment.contribution = request.POST['contribution']
                if 'publish_grades' in request.POST:
                    assignment.publish_grades = True
                else:
                    assignment.publish_grades = False
                assignment.save()
                return redirect(f'/manage/{param[0]}-{param[1]}/assignments')
            return render(request, 'edit_assignment.html', {'profile': profile, 'course': course, 'assignment': assignment})
    return redirect('login')


def delete_assignment(request, course, pk):
    if request.user.is_authenticated:
        profile = Profile.objects.get(username=request.user.username)
        if profile.userType == 'Student':
            return redirect('dashboard')
        else:
            param = course.split('-')
            course = Course.objects.get(semester_code=param[0], code=param[1])
            assignment = Assignment.objects.get(id=pk)
            if course.coordinators != profile or assignment.course.coordinators != profile:
                return redirect('dashboard')
            assignment.delete()
            return redirect(f'/manage/{param[0]}-{param[1]}/assignments')
    return redirect('login')

def manage_submissions(request, course):
    if request.user.is_authenticated:
        profile = Profile.objects.get(username=request.user.username)
        if profile.userType == 'Student':
            return redirect('dashboard')
        else:
            param = course.split('-')
            course = Course.objects.get(semester_code=param[0], code=param[1])
            if course.coordinators != profile:
                return redirect('dashboard')
            assignments = Assignment.objects.filter(course=course)
            return render(request, 'manage_submissions.html', {'profile': profile, 'course': course, 'assignments': assignments})
    return redirect('login')

def upload_submissions(request, course, pk):
    if request.user.is_authenticated:
        profile = Profile.objects.get(username=request.user.username)
        if profile.userType == 'Student':
            return redirect('dashboard')
        else:
            param = course.split('-')
            course = Course.objects.get(semester_code=param[0], code=param[1])
            assignment = Assignment.objects.get(id=pk)
            if course.coordinators != profile or assignment.course.coordinators != profile:
                return redirect('dashboard')
            submissions = Submission.objects.filter(assignment=assignment)
            grades = {}
            GRADES = Grade.objects.filter(assignment=assignment)
            for GRADE in GRADES:
                grades[GRADE.student.username] = GRADE.marks
            return render(request, 'upload_submissions.html', {'profile': profile, 'course': course, 'assignment': assignment, 'submissions': submissions, 'grades': grades})
    return redirect('login')

def save_submissions(request, course, pk, username):
    if request.user.is_authenticated:
        profile = Profile.objects.get(username=request.user.username)
        if profile.userType == 'Student':
            return redirect('dashboard')
        else:
            param = course.split('-')
            course = Course.objects.get(semester_code=param[0], code=param[1])
            assignment = Assignment.objects.get(id=pk)
            student = Profile.objects.get(username=username)
            if course.coordinators != profile or assignment.course.coordinators != profile:
                return redirect('dashboard')
            if request.method == 'POST':
                marks = request.POST['marks']
                if Grade.objects.filter(assignment=assignment, student=student).exists():
                    obj = Grade.objects.get(assignment=assignment, student=student)
                    obj.marks = marks
                    obj.save()
                else:
                    Grade.objects.create(assignment=assignment, student=student, marks=marks)
                return redirect(f'/manage/{param[0]}-{param[1]}/submissions/{assignment.id}')
            submission = Submission.objects.get(assignment=assignment, student=student)
            if Grade.objects.filter(assignment=assignment, student=student).exists():
                marks = Grade.objects.get(assignment=assignment, student=student).marks
            else:
                marks = 0.0
            return render(request, 'save_submissions.html', {'profile': profile, 'course': course, 'assignment': assignment, 'submission': submission, 'marks': marks, 'student': student})
    return redirect('login')

def manage_grades(request, course):
    if request.user.is_authenticated:
        profile = Profile.objects.get(username=request.user.username)
        if profile.userType == 'Student':
            return redirect('dashboard')
        else:
            param = course.split('-')
            course = Course.objects.get(semester_code=param[0], code=param[1])
            if course.coordinators != profile:
                return redirect('dashboard')
            if request.method == 'POST':
                read = request.FILES['csv_file']
                data = read.read().decode('utf-8')
                data = data.split('\n')
                for lines in data:
                    lines = lines.split(',')
                    try:
                        student = Profile.objects.get(username=lines[0])
                        if CourseGrade.objects.filter(course=course, student=student).exists():
                            obj = CourseGrade.objects.get(course=course, student=student)
                            if lines[1] == '-':
                                obj.delete()
                            else:
                                obj.grade = lines[1]
                                obj.save()
                        else:
                            CourseGrade.objects.create(course=course, student=student, grade=lines[1])
                        semesters = SemesterLog.objects.filter(student=student)
                        k = 1
                        for semester in semesters:
                            for past_course in semester.courses.all():
                                if past_course.semester_code == course.semester_code:
                                    semester.courses.add(course)
                                    k = 0
                                    break
                        if k == 1:
                            semester = SemesterLog.objects.create(number=len(semesters)+1, student=student)
                            semester.courses.add(course)
                            semester.save()
                    except:
                        pass
            participants = course.students.all().order_by('name', 'username')
            grades = {}
            for participant in participants:
                if CourseGrade.objects.filter(student=participant, course=course).exists():
                    grades[participant] = CourseGrade.objects.get(student=participant, course=course).grade
                else:
                    grades[participant] = '-'
            return render(request, 'manage_grades.html', {'profile': profile, 'course': course, 'grades': grades})
    return redirect('login')

def edit_grades(request, course, username):
    if request.user.is_authenticated:
        profile = Profile.objects.get(username=request.user.username)
        if profile.userType == 'Student':
            return redirect('dashboard')
        else:
            param = course.split('-')
            course = Course.objects.get(semester_code=param[0], code=param[1])
            student = Profile.objects.get(username=username)
            if course.coordinators != profile:
                return redirect('dashboard')
            if request.method == 'POST':
                grade = request.POST['grade']
                if CourseGrade.objects.filter(course=course, student=student).exists():
                    obj = CourseGrade.objects.get(course=course, student=student)
                    if grade == '-':
                        obj.delete()
                        return redirect(f'/manage/{param[0]}-{param[1]}/grades')
                    obj.grade = grade
                    obj.save()
                else:
                    CourseGrade.objects.create(course=course, student=student, grade=grade)
                semesters = SemesterLog.objects.filter(student=student)
                k = 1
                for semester in semesters:
                    for past_course in semester.courses.all():
                        if past_course.semester_code == course.semester_code:
                            semester.courses.add(course)
                            k = 0
                            break
                if k == 1:
                    semester = SemesterLog.objects.create(number=len(semesters)+1, student=student)
                    semester.courses.add(course)
                    semester.save()
                return redirect(f'/manage/{param[0]}-{param[1]}/grades')
            if CourseGrade.objects.filter(student=student, course=course).exists():
                grade = CourseGrade.objects.get(course=course, student=student).grade
            else:
                grade = '-'
            return render(request, 'edit_grades.html', {'profile': profile, 'course': course, 'assignment': assignment, 'grade': grade, 'student': student})
    return redirect('login')

def manage_participants(request, course):
    if request.user.is_authenticated:
        profile = Profile.objects.get(username=request.user.username)
        if profile.userType == 'Student':
            return redirect('dashboard')
        else:
            param = course.split('-')
            course = Course.objects.get(semester_code=param[0], code=param[1])
            if course.coordinators != profile:
                return redirect('dashboard')
            participants = course.students.all().order_by('name')
            return render(request, 'manage_participants.html', {'profile': profile, 'course': course, 'participants': participants})
    return redirect('login')

def messages(request):
    if request.user.is_authenticated:
        profile = Profile.objects.get(username=request.user.username)
        messages = []
        distinct = Message.objects.filter(message_from=profile).values('message_to').distinct()
        distinct = distinct.union(Message.objects.filter(message_to=profile).values('message_from').distinct())
        for dis in distinct:
            chat = Message.objects.filter(message_from=profile, message_to=dis['message_to'])
            chat = chat.union(Message.objects.filter(message_from=dis['message_to'], message_to=profile))
            messages.append(sorted(chat, key=operator.attrgetter('date_time'), reverse=True)[0])
        return render(request, 'messages.html', {'profile': profile, 'messages': messages})
    return redirect('login')

def message(request, user):
    if request.user.is_authenticated:
        profile = Profile.objects.get(username=request.user.username)
        second_user = Profile.objects.get(username=user)
        messages = []
        distinct = Message.objects.filter(message_from=profile).values('message_to').distinct()
        distinct = distinct.union(Message.objects.filter(message_to=profile).values('message_from').distinct())
        for dis in distinct:
            chat = Message.objects.filter(message_from=profile, message_to=dis['message_to'])
            chat = chat.union(Message.objects.filter(message_from=dis['message_to'], message_to=profile))
            messages.append(sorted(chat, key=operator.attrgetter('date_time'), reverse=True)[0])
        chat = Message.objects.filter(message_from=profile, message_to=second_user)
        chat = chat.union(Message.objects.filter(message_from=second_user, message_to=profile))
        return render(request, 'message.html', {'profile': profile, 'messages': messages, 'second_user': second_user, 'chat': chat})
    return redirect('login')

def settings(request):
    if request.user.is_authenticated:
        return render(request, 'settings.html')
    return redirect('login')

def login(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        if User.objects.filter(username=username).exists():
            user = auth.authenticate(username=username, password=password)
            if user:
                auth.login(request, user)
                return redirect('dashboard')
            else:
                return render(request, 'login.html', {'message':'Incorrect Password!'})
        else:
            return render(request, 'login.html', {'message':'User not found!'})
    return render(request, 'login.html')

def logout(request):
    if request.user.is_authenticated:
        auth.logout(request)
    return redirect('login')

@api_view(['POST'])
def dashboard_resources(request):
    if request.user.is_authenticated:
        profile = Profile.objects.get(username=request.user.username)
        sgpa_data = []
        cgpa_data = []
        labels = []
        credits = 0
        if SemesterLog.objects.filter(student=profile).exists():
            semesters = SemesterLog.objects.filter(student=profile).order_by('number')
            last_semester = semesters[len(semesters)-1]
            cgpa = last_semester.cgpa
            for i in range (len(semesters)):
                labels.append(f'Sem {i+1}')
            for semester in semesters:
                sgpa_data.append(semester.sgpa)
                cgpa_data.append(semester.cgpa)
                credits += semester.credits
        else:
            cgpa = 0
        return Response({'status': 200, 'cgpa': cgpa, 'labels': labels, 'sgpa_data': sgpa_data, 'cgpa_data': cgpa_data, 'credits': credits})
    return Response({'status': 401, 'message': 'Unauthorized!'})

@api_view(['POST'])
def send_message(request):
    if request.user.is_authenticated:
        data = request.data
        second_user = data.get('username')
        message = data.get('message')
        second_user = Profile.objects.get(username=second_user)
        profile = Profile.objects.get(username=request.user.username)
        message = Message.objects.create(message_from=profile, message_to=second_user, message=message)
        return Response({'status': 200, 'message': message.message, 'date_time': message.date_time})
    else:
        return Response({'status': 401, 'message': 'Unauthorized!'})

@api_view(['POST'])
def get_messages(request):
    if request.user.is_authenticated:
        data = request.data
        second_user = data.get('username')
        second_user = Profile.objects.get(username=second_user)
        profile = Profile.objects.get(username=request.user.username)
        chat = Message.objects.filter(message_from__in=[profile,second_user], message_to__in=[profile,second_user]).order_by('date_time')
        return Response({'status': 200, 'chat': list(chat.values())})
    else:
        return Response({'status': 401, 'message': 'Unauthorized!'})

@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)