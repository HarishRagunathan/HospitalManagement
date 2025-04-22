from django.shortcuts import render,redirect,HttpResponse
from dasapp.models import DoctorReg,Specialization,CustomUser,Appointment,Page,PatientReg
from django.http import JsonResponse
import random
from django.http import HttpResponseForbidden
from datetime import datetime
from django.contrib import messages
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth.decorators import login_required



def USERBASE(request):
    
    return render(request, 'userbase.html')



def PATIENTREGISTRATION(request):
    if request.method == "POST":
        pic = request.FILES.get('pic')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')
        mobno = request.POST.get('mobno')
        gender = request.POST.get('gender')
        username = request.POST.get('username')
        address = request.POST.get('address')
        password = request.POST.get('password')

        if CustomUser.objects.filter(email=email).exists():
            messages.warning(request,'Email already exist')
            return redirect('patreg')
        
        else:
            user = CustomUser(
               first_name=first_name,
               last_name=last_name,
               username=username,
               email=email,
               user_type=3,
               profile_pic = pic,
            )
            user.set_password(password)
            user.save()
            
            patient = PatientReg(
                admin = user,
                mobilenumber = mobno,
                gender = gender,
                address = address,
            )
            patient.save()            
            messages.success(request,'Signup Successfully')
            return redirect('patreg')
    

    return render(request, 'user/patient-reg.html')

def PATIENTHOME(request):
    doctor_count = DoctorReg.objects.all().count
    specialization_count = Specialization.objects.all().count
    context = {
        'doctor_count':doctor_count,
        'specialization_count':specialization_count,

    } 
    return render(request,'user/userhome.html',context)

def Index(request):
    doctorview = DoctorReg.objects.all()
    first_page = Page.objects.first()

    context = {'doctorview': doctorview,
               'dv': doctorview,
    'page':first_page,
    }
    return render(request, 'index.html',context)

def Doctor(request):
    doctorview = DoctorReg.objects.all()
    first_page = Page.objects.first()

    context = {'dv': doctorview,
    'page':first_page,
    }
    return render(request, 'doctor.html',context)

def Aboutus(request):
   
    first_page = Page.objects.first()

    context = {
    'page':first_page,
    }
    return render(request, 'aboutus.html',context)

def Contactus(request):
   
    first_page = Page.objects.first()

    context = {
    'page':first_page,
    }
    return render(request, 'contactus.html',context)

def get_doctor(request):
    if request.method == 'GET':
        s_id = request.GET.get('s_id')
        doctors = DoctorReg.objects.filter(specialization_id=s_id)
        
        doctor_options = ''
        for doc in doctors:
            doctor_options += f'<option value="{doc.id}">{doc.admin.first_name}</option>'
        
        return JsonResponse({'doctor_options': doctor_options})



from datetime import datetime, timedelta
from django.utils import timezone
from django.contrib import messages
import random

# Utility to parse time with multiple format options
def parse_time_string(time_str):
    formats = ['%H:%M', '%H:%M:%S', '%H:%M:%S.%f']
    for fmt in formats:
        try:
            return datetime.strptime(time_str, fmt).time()
        except ValueError:
            continue
    raise ValueError("Unsupported time format")

def create_appointment(request):
    specialization = Specialization.objects.all()

    if request.method == "POST":
        try:
            # Generate appointment number
            appointmentnumber = random.randint(100000000, 999999999)

            # Get posted data
            spec_id = request.POST.get('spec_id')
            doctor_id = request.POST.get('doctor_id')
            date_str = request.POST.get('date_of_appointment')  # string format
            time_str = request.POST.get('time_of_appointment')
            additional_msg = request.POST.get('additional_msg')

            # Convert to proper date & time objects
            try:
                appointment_date = datetime.strptime(date_str, '%Y-%m-%d').date()
                appointment_time = parse_time_string(time_str)
            except ValueError:
                messages.error(request, "Invalid date or time format.")
                return redirect('patientappointment')

            # Validate future date
            if appointment_date <= timezone.now().date():
                messages.error(request, "Please select a future date for the appointment.")
                return redirect('patientappointment')

            # Get model instances
            doc_instance = DoctorReg.objects.get(id=doctor_id)
            spec_instance = Specialization.objects.get(id=spec_id)
            patient_instance = PatientReg.objects.get(admin=request.user.id)

            # Combine date & time
            requested_datetime = datetime.combine(appointment_date, appointment_time)

            # Check existing appointments for time conflict
            existing_appointments = Appointment.objects.filter(
                doctor_id=doc_instance,
                date_of_appointment=date_str  # stored as CharField, compare with string
            )

            for appt in existing_appointments:
                existing_time = parse_time_string(str(appt.time_of_appointment))
                existing_datetime = datetime.combine(appointment_date, existing_time)
                time_diff = abs((requested_datetime - existing_datetime).total_seconds()) / 60

                if time_diff < 15:
                    messages.error(request, "This doctor already has an appointment within 15 minutes of your selected time.")
                    return redirect('patientappointment')

            # Create the appointment
            Appointment.objects.create(
                appointmentnumber=appointmentnumber,
                pat_id=patient_instance,
                spec_id=spec_instance,
                doctor_id=doc_instance,
                date_of_appointment=date_str,  # saved as string
                time_of_appointment=time_str,
                additional_msg=additional_msg
            )

            messages.success(request, "Your appointment request has been sent. We will contact you soon.")
            return redirect('patientappointment')

        except DoctorReg.DoesNotExist:
            messages.error(request, "Selected doctor does not exist.")
        except Specialization.DoesNotExist:
            messages.error(request, "Selected specialization does not exist.")
        except PatientReg.DoesNotExist:
            messages.error(request, "Patient profile not found.")
        except Exception as e:
            messages.error(request, f"An error occurred: {str(e)}")
            return redirect('patientappointment')

    return render(request, 'user/appointment.html', {'specialization': specialization})






def View_Appointment_History(request):
    pat_reg = request.user
    pat_admin = PatientReg.objects.get(admin=pat_reg)
    userapptdetails = Appointment.objects.filter(pat_id=pat_admin)
    context = {
        'vah':userapptdetails
    }
    return render(request, 'user/appointment-history.html', context)

def cancel_appointment(request, id):
    try:
        appointment = Appointment.objects.get(id=id, pat_id=request.user.patientreg)
        if appointment.status != 'Approved':
            appointment.status = 'Canceled'
            appointment.save()
            messages.success(request, "Your appointment has been canceled successfully.")
        else:
            messages.error(request, "You cannot cancel this appointment.")
    except Appointment.DoesNotExist:
        messages.error(request, "Appointment not found.")
    return redirect('view_appointment_history')

def User_Search_Appointments(request):
    page = Page.objects.all()
    
    if request.method == "GET":
        query = request.GET.get('query', '')
        if query:
            # Filter records where fullname or Appointment Number contains the query
            patient = Appointment.objects.filter(fullname__icontains=query) | Appointment.objects.filter(appointmentnumber__icontains=query)
            messages.info(request, "Search against " + query)
            context = {'patient': patient, 'query': query, 'page': page}
            return render(request, 'search-appointment.html', context)
        else:
            print("No Record Found")
            context = {'page': page}
            return render(request, 'search-appointment.html', context)
    
    # If the request method is not GET
    context = {'page': page}
    return render(request, 'search-appointment.html', context)
def View_Appointment_Details(request,id):
    page = Page.objects.all()
    patientdetails=Appointment.objects.filter(id=id)
    context={'patientdetails':patientdetails,
    'page': page

    }

    return render(request,'user_appointment-details.html',context)







