from django.db import models
from academic_main.models import School
from stu_main.models import Teacher
from django.core.validators import MinValueValidator
from django.utils import timezone

# Create your models here.

class ExpenseCategory(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name='expense_categories')

    class Meta:
        verbose_name_plural = "Expense Categories"
        unique_together = ('name', 'school')

    def __str__(self):
        return f"{self.name} - {self.school.name}"

class Expense(models.Model):
    PAYMENT_STATUS = (
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('cancelled', 'Cancelled'),
    )

    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name='expenses')
    category = models.ForeignKey(ExpenseCategory, on_delete=models.SET_NULL, null=True, related_name='expenses')
    amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    description = models.TextField()
    date = models.DateField()
    payment_status = models.CharField(max_length=10, choices=PAYMENT_STATUS, default='pending')
    payment_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    receipt = models.FileField(upload_to='expense_receipts/', null=True, blank=True)

    def __str__(self):
        return f"{self.category.name if self.category else 'Uncategorized'} - {self.amount} ({self.date})"

class TeacherSalaryPayment(models.Model):
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE, related_name='salary_payments')
    expense = models.OneToOneField(Expense, on_delete=models.CASCADE, related_name='teacher_salary')
    month = models.DateField(help_text="The month for which the salary is being paid")
    basic_salary = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    allowances = models.DecimalField(max_digits=10, decimal_places=2, default=0, validators=[MinValueValidator(0)])
    deductions = models.DecimalField(max_digits=10, decimal_places=2, default=0, validators=[MinValueValidator(0)])
    comments = models.TextField(blank=True)

    class Meta:
        unique_together = ('teacher', 'month')

    def __str__(self):
        return f"Salary Payment - {self.teacher} - {self.month.strftime('%B %Y')}"

    @property
    def net_salary(self):
        return self.basic_salary + self.allowances - self.deductions

    def save(self, *args, **kwargs):
        # Update or create associated expense
        if not self.expense_id:
            category, _ = ExpenseCategory.objects.get_or_create(
                name='Teacher Salary',
                school=self.teacher.school,
                defaults={'description': 'Teacher salary payments'}
            )
            self.expense = Expense.objects.create(
                school=self.teacher.school,
                category=category,
                amount=self.net_salary,
                description=f"Salary payment for {self.teacher} - {self.month.strftime('%B %Y')}",
                date=self.month,
            )
        else:
            self.expense.amount = self.net_salary
            self.expense.description = f"Salary payment for {self.teacher} - {self.month.strftime('%B %Y')}"
            self.expense.save()
        
        super().save(*args, **kwargs)

class Announcement(models.Model):
    PRIORITY_CHOICES = (
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
    )

    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name='announcements')
    title = models.CharField(max_length=200)
    content = models.TextField()
    created_by = models.ForeignKey('stu_main.CustomUser', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')
    is_active = models.BooleanField(default=True)
    expiry_date = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    @property
    def is_expired(self):
        if self.expiry_date:
            return timezone.now() > self.expiry_date
        return False
