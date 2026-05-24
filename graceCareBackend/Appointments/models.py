from django.db import models
import uuid
# Create your models here.
class Appointment(models.Model):
    appointment_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    doctor = models.ForeignKey('Users.User', on_delete=models.CASCADE, related_name='doctor_appointments')
    doctor_specialization = models.CharField(max_length=30, blank=True, null=True)
    patient = models.ForeignKey('Users.User', on_delete=models.CASCADE, related_name='patient_appointments')
    type_of_appointment = models.CharField(max_length=20, blank=True, null=True)
    appointment_date = models.DateField()
    appointment_time = models.TimeField()
    fee_of_appointment = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    reason_for_appointment = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Appointment {self.appointment_id} between Dr. {self.doctor.first_name} and {self.patient.first_name} on {self.appointment_date} at {self.appointment_time}"