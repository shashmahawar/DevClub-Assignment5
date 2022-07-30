from django.db import models

# Create your models here.

class Profile(models.Model):
    username = models.CharField(max_length=150)
    email = models.EmailField(max_length=255)
    name = models.CharField(max_length=150)
    USER_CHOICES = [
        ('Student', 'Student'),
        ('Faculty', 'Faculty'),
        ('Admin', 'Admin'),
    ]
    userType = models.CharField(max_length=10, choices=USER_CHOICES)
    image = models.ImageField(upload_to='profile_pictures', default='profile_pictures/default.png')

    def __str__(self):
        return self.username

class Course(models.Model):
    code = models.CharField(max_length=10)
    semester_code = models.CharField(max_length=10)
    icon = models.ImageField(upload_to='course_icons')
    name = models.CharField(max_length=255)
    coordinators = models.ForeignKey(Profile, related_name='course_coordinator', on_delete=models.CASCADE)
    slot = models.CharField(max_length=1)
    credits = models.FloatField()
    credit_structure = models.CharField(max_length=10)
    department = models.CharField(max_length=100)
    prerequisite = models.ForeignKey('self', null=True, blank=True, on_delete=models.CASCADE)
    students = models.ManyToManyField(Profile, related_name='course_students')
    course_intro = models.FileField(upload_to='course_intro')
    publish_grades = models.BooleanField(default=False)

    def __str__(self):
        return f'{self.semester_code} - {self.code}'

class Assignment(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    max_marks = models.FloatField()
    content = models.TextField(max_length=1000)
    assignment = models.FileField(upload_to='assignments', blank=True)
    due_date = models.DateTimeField()
    contribution = models.FloatField()
    publish_grades = models.BooleanField(default=False)

class Submission(models.Model):
    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    student = models.ForeignKey(Profile, on_delete=models.CASCADE)
    submitted_at = models.DateTimeField(auto_now_add=True)
    submission = models.FileField(upload_to='submissions')

class Grade(models.Model):
    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE)
    student = models.ForeignKey(Profile, on_delete=models.CASCADE)
    marks = models.FloatField()

class CourseGrade(models.Model):
    student = models.ForeignKey(Profile, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    GRADE_CHOICES = [
        ('A', 'A'),
        ('A-', 'A-'),
        ('B', 'B'),
        ('B-', 'B-'),
        ('C', 'C'),
        ('C-', 'C-'),
        ('D', 'D'),
    ]
    grade = models.CharField(max_length=2, choices=GRADE_CHOICES)

    def __str__(self):
        return f'{self.course.code} - {self.student.username}'

class SemesterLog(models.Model):
    number = models.IntegerField()
    student = models.ForeignKey(Profile, on_delete=models.CASCADE)
    courses = models.ManyToManyField(Course)
    @property
    def credits(self):
        n = 0
        for course in self.courses.all():
            if course.publish_grades:
                n += course.credits
        return n
    @property
    def sgpa(self):
        n = 0
        p = 0
        keys = {'A':10,'A-':9,'B':8,'B-':7,'C':6,'C-':5,'D':4}
        for course in self.courses.all():
            if course.publish_grades:
                n += course.credits
                grade = CourseGrade.objects.get(student=self.student, course=course).grade
                p += keys[grade]*course.credits
        if n == 0:
            return 0
        return round(p/n,3)
    @property
    def cgpa(self):
        n = 0
        p = 0
        keys = {'A':10,'A-':9,'B':8,'B-':7,'C':6,'C-':5,'D':4}
        for course in self.courses.all():
            if course.publish_grades:
                n += course.credits
                grade = CourseGrade.objects.get(student=self.student, course=course).grade
                p += keys[grade]*course.credits
        if n == 0:
            return 0
        sgpa = round(p/n,3)
        if self.number == 1:
            return sgpa
        else:
            t = sgpa * n
            c = n
            past_sems = SemesterLog.objects.filter(student=self.student, number__lt=self.number)
            for past_sem in past_sems:
                t += past_sem.sgpa * past_sem.credits
                c += past_sem.credits
            return round(t/c,3)

class Message(models.Model):
    message_from = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='message_from')
    message_to = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='message_to')
    date_time = models.DateTimeField(auto_now_add=True)
    message = models.TextField(max_length=2000)

class Announcement(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    title = models.CharField(max_length=100)
    description = models.TextField(max_length=2000)

class Material(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    title = models.CharField(max_length=100)
    material = models.FileField(upload_to='course_materials')