from django.shortcuts import render, redirect
from django.urls import reverse_lazy, reverse
import subprocess
from django.views.generic.edit import FormView, CreateView
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.conf import settings
from .forms import SignUpForm, ForgotPasswordForm, OTPVerifyForm, ResetPasswordForm
from .models import PasswordResetOTP
from .utils import generate_otp
from django.contrib import messages

# Create your views here.

class SignUpView(CreateView):
    form_class = SignUpForm
    success_url = reverse_lazy('login')
    template_name = 'registration/signup.html'

def get_kubectl_data(command):
    try:
        result = subprocess.run(command, capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            return result.stdout
    except Exception:
        pass
    return None

def fetch_tas_pods_data():
    # Attempt to fetch live data for pods labeled with app=tas
    # We'll use multiple commands to piece together the full picture
    
    # 1. Get Pod Info (status, node, ip)
    pods_raw = get_kubectl_data(['kubectl', 'get', 'pods', '-n', 'tas', '-l', 'statefulset.kubernetes.io/pod-name', '-o', 'wide', '--no-headers'])
    
    # 2. Get Metrics (CPU, Memory)
    metrics_raw = get_kubectl_data(['kubectl', 'top', 'pods', '-n', 'tas', '-l', 'statefulset.kubernetes.io/pod-name', '--no-headers'])
    
    # 3. Get Node Statuses
    # Output format: NAME, STATUS, ROLES, AGE, VERSION, INTERNAL-IP, EXTERNAL-IP, OS-IMAGE, KERNEL-VERSION, CONTAINER-RUNTIME
    nodes_raw = get_kubectl_data(['kubectl', 'get', 'nodes', '--no-headers'])
    
    node_status_map = {}
    if nodes_raw:
        for line in nodes_raw.strip().split('\n'):
            parts = line.split()
            if len(parts) >= 2:
                node_status_map[parts[0]] = parts[1]

    metrics_map = {}
    if metrics_raw:
        for line in metrics_raw.strip().split('\n'):
            parts = line.split()
            if len(parts) >= 3:
                metrics_map[parts[0]] = {'cpu': parts[1], 'memory': parts[2]}

    processed_pods = []
    
    if pods_raw:
        for line in pods_raw.strip().split('\n'):
            parts = line.split()
            if len(parts) >= 7:
                name = parts[0]
                status = parts[2]
                restarts = parts[3]
                pod_ip = parts[5]
                node_name = parts[6]
                
                pod_metrics = metrics_map.get(name, {'cpu': '0m', 'memory': '0Mi'})
                node_status = node_status_map.get(node_name, 'Unknown')
                
                # Calculate numeric percentages for gauges
                cpu_val = pod_metrics['cpu']
                cpu_percent = 15 # default
                if 'm' in cpu_val:
                    try:
                        val = int(cpu_val.replace('m', ''))
                        cpu_percent = min(100, max(5, int(val / 10))) # Scale 1000m to 100%
                    except: pass
                
                mem_val = pod_metrics['memory']
                mem_percent = 20 # default
                if 'Mi' in mem_val:
                    try:
                        val = int(mem_val.replace('Mi', ''))
                        mem_percent = min(100, max(5, int(val / 10))) # Scale 1024Mi to 100%
                    except: pass

                processed_pods.append({
                    "name": name,
                    "status": status,
                    "restarts": restarts,
                    "ip": pod_ip,
                    "node": node_name,
                    "node_status": node_status,
                    "cpu": cpu_val,
                    "cpu_percent": cpu_percent,
                    "memory": mem_val,
                    "mem_percent": mem_percent,
                    "namespace": "tas"
                })
    
    # Fallback to Mock Data if no real pods found (for demo/dev)
    if not processed_pods:
        processed_pods = [
            {"name": "tas-0", "status": "Running", "restarts": "0", "ip": "10.244.1.23", "node": "node-01", "node_status": "Ready", "cpu": "125m", "cpu_percent": 12, "memory": "256Mi", "mem_percent": 25, "namespace": "tas"},
            {"name": "tas-1", "status": "Running", "restarts": "2", "ip": "10.244.1.24", "node": "node-02", "node_status": "Ready", "cpu": "450m", "cpu_percent": 45, "memory": "512Mi", "mem_percent": 50, "namespace": "tas"},
            {"name": "tas-2", "status": "Pending", "restarts": "0", "ip": "Pending", "node": "-", "node_status": "-", "cpu": "0m", "cpu_percent": 5, "memory": "0Mi", "mem_percent": 5, "namespace": "tas"},
            {"name": "tas-3", "status": "Running", "restarts": "0", "ip": "10.244.1.25", "node": "node-01", "node_status": "Ready", "cpu": "85m", "cpu_percent": 8, "memory": "128Mi", "mem_percent": 12, "namespace": "tas"},
        ]
        
    return processed_pods

@login_required
def home(request):
    pods = fetch_tas_pods_data()
    
    context = {
        "pods": pods,
        "total_pods": len(pods),
        "running_pods": sum(1 for p in pods if p['status'] == 'Running'),
        "failed_pods": sum(1 for p in pods if p['status'] in ['Failed', 'Error', 'CrashLoopBackOff']),
        "app_name": "TAS (Telecom App Server)"
    }
    return render(request, 'core/home.html', context)


@login_required
def node_monitor(request):
    try:
        # Run kubectl command
        result = subprocess.run(
            ['kubectl', 'get', 'nodes', '-A', '-o', 'wide'],
            capture_output=True,
            text=True,
            timeout=10
        )
        output = result.stdout if result.returncode == 0 else result.stderr
        
        # If output is empty but return code is 0, provide a helper message
        if not output and result.returncode == 0:
            output = "No nodes found or command returned empty output."
            
    except Exception as e:
        output = f"Error executing kubectl: {str(e)}"

    return render(request, 'core/node_monitor.html', {'output': output})

class ForgotPasswordView(FormView):
    template_name = 'core/forgot_password.html'
    form_class = ForgotPasswordForm
    success_url = reverse_lazy('verify_otp')

    def form_valid(self, form):
        email = form.cleaned_data['email']
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            # Don't reveal user existence, but for this demo we can just fail silently or show generic message
            messages.info(self.request, "If that email exists, we sent an OTP.")
            return super().form_valid(form)

        # Generate and Save OTP
        otp_code = generate_otp()
        PasswordResetOTP.objects.create(user=user, otp_code=otp_code)

        # Send Email
        send_mail(
            'Password Reset OTP',
            f'Your OTP is: {otp_code}',
            'noreply@officesuite.com',
            [email],
            fail_silently=False,
        )
        
        # Store email in session for next step
        self.request.session['reset_email'] = email
        return super().form_valid(form)

class VerifyOTPView(FormView):
    template_name = 'core/verify_otp.html'
    form_class = OTPVerifyForm
    success_url = reverse_lazy('reset_password')

    def form_valid(self, form):
        otp_input = form.cleaned_data['otp_code']
        email = self.request.session.get('reset_email')
        
        if not email:
            return redirect('forgot_password')

        try:
            user = User.objects.get(email=email)
            # Check latest OTP
            otp_obj = PasswordResetOTP.objects.filter(user=user).order_by('-created_at').first()
            
            if otp_obj and otp_obj.otp_code == otp_input and otp_obj.is_valid():
                # OTP Valid
                self.request.session['reset_allowed'] = True
                return super().form_valid(form)
            else:
                form.add_error('otp_code', 'Invalid or expired OTP.')
                return self.form_invalid(form)

        except User.DoesNotExist:
            return redirect('forgot_password')

class ResetPasswordView(FormView):
    template_name = 'core/reset_password.html'
    form_class = ResetPasswordForm
    success_url = reverse_lazy('login')

    def dispatch(self, request, *args, **kwargs):
        if not request.session.get('reset_allowed'):
            return redirect('forgot_password')
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        email = self.request.session.get('reset_email')
        user = User.objects.get(email=email)
        
        new_pass = form.cleaned_data['new_password']
        user.set_password(new_pass)
        user.save()
        
        # Clean session
        del self.request.session['reset_email']
        del self.request.session['reset_allowed']
        
        messages.success(self.request, "Password reset successful. Please login.")
        return super().form_valid(form)
