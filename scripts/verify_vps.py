#!/usr/bin/env python3
"""
Quick DNS and VPS Verification Script
Run this before deployment to verify everything is ready
"""

import socket
import subprocess
import sys

def check_dns(domain):
    """Check if domain resolves to an IP"""
    print(f"\n🔍 Checking DNS for {domain}...")
    try:
        ip = socket.gethostbyname(domain)
        print(f"✅ {domain} resolves to: {ip}")
        return ip
    except socket.gaierror:
        print(f"❌ {domain} does not resolve to any IP")
        print("   Please configure DNS in Hostinger panel")
        return None

def check_ssh(ip, username="root"):
    """Check if SSH is accessible"""
    print(f"\n🔍 Checking SSH access to {ip}...")
    print(f"   Attempting: ssh {username}@{ip}")
    print("   (This will timeout if not accessible)")
    
    try:
        result = subprocess.run(
            ["ssh", "-o", "ConnectTimeout=5", "-o", "StrictHostKeyChecking=no", 
             f"{username}@{ip}", "echo 'SSH OK'"],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0:
            print(f"✅ SSH is accessible")
            return True
        else:
            print(f"⚠️  SSH connection failed")
            print(f"   You may need to:")
            print(f"   1. Accept host key fingerprint")
            print(f"   2. Enter password")
            print(f"   Try manually: ssh {username}@{ip}")
            return False
    except subprocess.TimeoutExpired:
        print(f"❌ SSH connection timed out")
        print(f"   Server may be down or firewall blocking port 22")
        return False
    except FileNotFoundError:
        print(f"⚠️  SSH client not found on this system")
        print(f"   Install OpenSSH or use PuTTY on Windows")
        return False

def check_http(domain):
    """Check if HTTP is accessible"""
    print(f"\n🔍 Checking HTTP access to {domain}...")
    try:
        import urllib.request
        url = f"http://{domain}"
        response = urllib.request.urlopen(url, timeout=10)
        print(f"✅ HTTP is accessible (Status: {response.status})")
        return True
    except Exception as e:
        print(f"⚠️  HTTP not accessible yet (expected before deployment)")
        print(f"   This is normal if you haven't deployed yet")
        return False

def main():
    print("="*60)
    print("🚀 YTZ Automation - Pre-Deployment Verification")
    print("="*60)
    
    domain = "za.omysha.org"
    
    # Step 1: Check DNS
    ip = check_dns(domain)
    if not ip:
        print("\n❌ FAILED: DNS not configured")
        print("\nNext steps:")
        print("1. Log in to Hostinger")
        print("2. Go to DNS settings")
        print("3. Add A record:")
        print(f"   Name: za")
        print(f"   Type: A")
        print(f"   Value: [Your VPS IP]")
        print("4. Wait 5-10 minutes for propagation")
        print("5. Run this script again")
        sys.exit(1)
    
    # Step 2: Check SSH
    print(f"\n📝 VPS IP Address: {ip}")
    print(f"   Save this for deployment!")
    
    ssh_ok = check_ssh(ip)
    
    # Step 3: Check HTTP (optional)
    check_http(domain)
    
    # Summary
    print("\n" + "="*60)
    print("📋 SUMMARY")
    print("="*60)
    print(f"Domain: {domain}")
    print(f"IP Address: {ip}")
    print(f"DNS Status: ✅ Configured")
    print(f"SSH Status: {'✅ Accessible' if ssh_ok else '⚠️  Check manually'}")
    
    if ssh_ok:
        print("\n✅ READY FOR DEPLOYMENT!")
        print("\nNext steps:")
        print(f"1. Connect: ssh root@{ip}")
        print("2. Follow HOSTINGER_DEPLOYMENT.md")
    else:
        print("\n⚠️  VERIFY SSH ACCESS")
        print("\nNext steps:")
        print(f"1. Try manually: ssh root@{ip}")
        print("2. If prompted, accept host key")
        print("3. Enter password from Hostinger panel")
        print("4. Once connected, follow HOSTINGER_DEPLOYMENT.md")
    
    print("\n" + "="*60)

if __name__ == "__main__":
    main()
