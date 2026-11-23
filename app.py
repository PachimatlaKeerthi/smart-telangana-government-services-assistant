from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
import re
import secrets
import hashlib
import os
import smtplib
from dotenv import load_dotenv

load_dotenv()

from datetime import datetime, timedelta, timezone
from email.message import EmailMessage
from database import (
    initialize_database,
    create_users_table,
    add_user,
    get_user_by_email,
    update_user_password,
    create_password_resets_table,
    save_password_reset,
    get_password_reset,
    delete_password_reset,
    get_all_categories,
    get_category_data,
    get_service_data,
    search_database,
    get_service_data,
    search_database,
    create_favorites_table,
    add_favorite,
    get_user_favorites,
    remove_favorite
)
app = Flask(__name__)

app.secret_key = os.getenv("SECRET_KEY")
if not app.secret_key:
    raise RuntimeError("SECRET_KEY is missing. Check your .env file.")
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["SESSION_COOKIE_SECURE"] = False
from flask_wtf.csrf import CSRFProtect

csrf = CSRFProtect(app)


create_users_table()
create_password_resets_table()
create_favorites_table()

def send_reset_email(receiver_email, reset_link):

    sender_email = os.getenv("GMAIL_ADDRESS")
    app_password = os.getenv("GMAIL_APP_PASSWORD")

    if not sender_email or not app_password:
        raise RuntimeError("Email settings are not configured.")

    message = EmailMessage()
    message["Subject"] = "Password Reset - Smart Telangana Services"
    message["From"] = sender_email
    message["To"] = receiver_email

    message.set_content(
        f"""Hello,

We received a request to reset your password.

Use the link below to reset your password:

{reset_link}

This link expires in 15 minutes.

If you did not request this, ignore this email.

Thank you.
Smart Telangana Government Services Assistant
"""
    )

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(sender_email, app_password)
        server.send_message(message)



# ============================================================
# TELANGANA GOVERNMENT SERVICES
# This is an independent student-developed information project.
# It is not an official Telangana Government website.
# ============================================================

services = {
    'scholarship': {
        'name': 'Telangana ePASS Scholarships',
        'description': 'Information about Telangana scholarship services for eligible students.',
        'notice': 'Check the official Telangana ePASS portal for current details.',
        'details': [
            'Pre-matric scholarship information',
            'Post-matric scholarship information',
            'Required documents and details',
            'Application status information'
        ],
        'portal_name': 'Telangana ePASS',
        'portal_instructions': [
            'Open the official Telangana ePASS website.',
            'Select the applicable pre-matric or post-matric scholarship service.',
            'Read the eligibility conditions and required documents.',
            'Register or log in and follow the application instructions.',
            'Use the application status option to track your application.'
        ],
        'official_url': 'https://telanganaepass.cgg.gov.in/'
    },
'jobs': {
    'name': 'Telangana Government Jobs',
    'description': 'Find information about Telangana government recruitment.',
    'notice': 'Check the official TGPSC website for recruitment notifications.',
    'details': [
        'Government job notifications',
        'Eligibility and recruitment information',
        'Application information',
        'Examination updates'
    ],
    'portal_name': 'Telangana Public Service Commission (TGPSC)',
    'portal_instructions': [
        'Open the official TGPSC website.',
        'Select the Notifications section.',
        'Read the recruitment notification carefully.',
        'Check eligibility, age limit and required qualifications.',
        'Follow the online application instructions.',
        'Check the website regularly for examination updates and results.'
    ],
    'official_url': 'https://websitenew.tgpsc.gov.in/'
},
 'pension': {'name': 'Telangana Pension Services',
             'description': 'Information about pension and social security services.',
             'notice': 'Check the official portal for current scheme information.',
             'details': ['Pension scheme information',
                         'Application information',
                         'Required documents and details',
                         'Application status information'],
            'portal_name': 'Telangana Cheyutha',
'portal_instructions': [
    'Open the official Telangana Cheyutha website.',
    'Review the available social security pension schemes.',
    'Check the eligibility conditions for the relevant pension.',
    'Read the required documents and application procedure.',
    'Follow the official instructions to check application status.'
],
'official_url': 'https://www.cheyutha.telangana.gov.in/'},
 'bus-pass': {'name': 'TGSRTC Bus Pass',
              'description': 'Information about Telangana RTC bus pass services.',
              'notice': 'Check the official TGSRTC website for current services.',
              'details': ['Student bus pass information',
                          'General bus pass information',
                          'Application and renewal information',
                          'Bus pass service details'],
             'portal_name': 'TGSRTC',
'portal_instructions': [
    'Open the official TGSRTC website.',
    'Select the applicable student or general bus pass service.',
    'Check eligibility, required documents and current fees.',
    'Follow the online application or renewal instructions.',
    'Contact the nearest TGSRTC bus pass counter if assistance is needed.'
],
'official_url': 'https://tgsrtc.telangana.gov.in/bus-pass-services'},
'farmer': {
    'name': 'Telangana Rythu Bharosa',
    'description': 'Information about Telangana farmer support services.',
    'notice': 'Check the official portal for current scheme information.',
    'details': [
        'Farmer support scheme information',
        'Eligibility information',
        'Application and beneficiary details',
        'Official scheme updates'
    ],
    'portal_name': 'Telangana Rythu Bharosa',
'portal_instructions': [
    'Open the official Telangana Rythu Bharosa website.',
    'Read the latest scheme guidelines and eligibility conditions.',
    'Check the official information about farmer benefits.',
    'Follow the instructions published by the Agriculture Department.',
    'Contact your local Agriculture Officer if you need assistance.'
],
'official_url': 'https://rythubharosa.telangana.gov.in/'
},
 'health': {'name': 'Telangana Aarogyasri',
            'description': 'Information about Telangana Aarogyasri healthcare services.',
            'notice': 'Check the official portal for current scheme and hospital information.',
            'details': ['Healthcare scheme information',
                        'Covered treatment information',
                        'Network hospital information',
                        'Official scheme details'],
            'portal_name': 'Telangana Aarogyasri',
'portal_instructions': [
    'Open the official Telangana Aarogyasri website.',
    'Review the healthcare scheme information.',
    'Check the list of covered treatments and network hospitals.',
    'Contact the relevant network hospital to confirm eligibility.',
    'Follow the hospital instructions for accessing scheme benefits.'
],
'official_url': 'https://rajivaarogyasri.telangana.gov.in/ASRI2.0/'},
 'income-certificate': {'name': 'Income Certificate',
                        'description': 'Information about applying for an Income Certificate '
                                       'through the Telangana Revenue Department.',
                        'notice': 'An Income Certificate is issued by the competent Revenue '
                                  'authority after verification of the application and relevant '
                                  'income details.',
                        'details': ['Income Certificate application information',
                                    'ISES-Income Certificate service information',
                                    'Income details from applicable sources',
                                    'Required supporting documents',
                                    'Application verification process',
                                    'Application status information'],
                        'portal_name': 'Telangana MeeSeva - Revenue Department',
                        'portal_instructions': ['Visit the official Telangana MeeSeva portal. '
                                                'Search for ISES-Income Certificate or Income '
                                                'Certificate under Revenue Department services. '
                                                'Check the applicable eligibility conditions and '
                                                'required documents before submitting your '
                                                'application. Keep your application number for '
                                                'future reference.'],
                        'official_url': 'https://ts.meeseva.telangana.gov.in/meeseva/home.htm'},
 'caste-certificate': {'name': 'Caste Certificate',
                       'description': 'Information about applying for a Caste or Integrated '
                                      'Certificate through the Telangana Revenue Department.',
                       'notice': 'The Telangana Revenue Department provides Integrated Certificate '
                                 'services covering Caste, Nativity and Date of Birth. The '
                                 'applicable service and verification requirements depend on the '
                                 "applicant's circumstances.",
                       'details': ['Caste Certificate application information',
                                   'Integrated Caste, Nativity and Date of Birth Certificate',
                                   'Community-specific certificate information',
                                   'Required supporting documents',
                                   'Application verification process',
                                   'Application status information'],
                       'portal_name': 'Telangana MeeSeva - Revenue Department',
                       'portal_instructions': ['Visit the official Telangana MeeSeva portal and '
                                               'search for Integrated Certificate '
                                               '(Caste-Nativity-Date of Birth) or the applicable '
                                               'ISES-Integrated Certificate service. Check the '
                                               'available community options, eligibility '
                                               'conditions and required documents before applying. '
                                               'Contact a MeeSeva centre if you are unsure which '
                                               'service applies to you.'],
                       'official_url': 'https://ts.meeseva.telangana.gov.in/meeseva/home.htm'},
 'residence-certificate': {'name': 'Residence Certificate',
                           'description': 'Information about applying for a Residence Certificate '
                                          'through the Telangana Revenue Department.',
                           'notice': 'The Telangana MeeSeva service catalogue lists ISES-Residence '
                                     'Certificate and Residence Certificate-General services. '
                                     'Applicants should select the applicable service according to '
                                     'their requirements.',
                           'details': ['Residence Certificate application information',
                                       'ISES-Residence Certificate service',
                                       'Residence Certificate-General service',
                                       'Identity and address proof information',
                                       'Required supporting documents',
                                       'Application verification and status information'],
                           'portal_name': 'Telangana MeeSeva - Revenue Department',
                           'portal_instructions': ['Visit the official Telangana MeeSeva portal '
                                                   'and search for ISES-Residence Certificate or '
                                                   'Residence Certificate-General. Select the '
                                                   'applicable service according to your '
                                                   'requirement. Check the eligibility conditions '
                                                   'and required identity and address proofs '
                                                   'before submitting your application.'],
                           'official_url': 'https://ts.meeseva.telangana.gov.in/meeseva/home.htm'},
 'birth-certificate': {'name': 'Birth Certificate',
                       'description': 'Information about birth registration, Birth Certificate '
                                      'services, corrections and child name inclusion in '
                                      'Telangana.',
                       'notice': 'Birth registration and certificate services are handled by the '
                                 'relevant local registration authority. GHMC handles records '
                                 'within Greater Hyderabad, while CDMA provides services for areas '
                                 'outside GHMC covered by CDMA. For rural records, contact the '
                                 'relevant local Registrar of Births and Deaths.',
                       'details': ['Birth Certificate application information',
                                   'Search for already registered birth records',
                                   'Birth Certificate correction services',
                                   'Child name inclusion information',
                                   'Non-availability of Birth Certificate',
                                   'Late birth registration information',
                                   'Application status information'],
                       'portal_name': 'Telangana MeeSeva - Birth Certificate Services',
                       'portal_instructions': ['Visit the official Telangana MeeSeva portal and '
                                               'search for Birth Certificate services. Choose GHMC '
                                               'for records within GHMC limits or CDMA for '
                                               'municipal records outside GHMC. For rural records, '
                                               'contact the relevant local registration authority. '
                                               'Birth corrections, child name inclusion, '
                                               'non-availability certificates and late '
                                               'registration are separate services. Check the '
                                               'applicable requirements before applying.'],
                       'official_url': 'https://ts.meeseva.telangana.gov.in/meeseva/home.htm'},
 'death-certificate': {'name': 'Death Certificate',
                       'description': 'Information about death registration, Death Certificate '
                                      'services, corrections and non-availability certificates in '
                                      'Telangana.',
                       'notice': 'Death registration and certificate services are handled by the '
                                 'relevant local registration authority. GHMC handles records '
                                 'within Greater Hyderabad, while CDMA provides services for areas '
                                 'outside GHMC covered by CDMA. For rural records, contact the '
                                 'relevant local Registrar of Births and Deaths.',
                       'details': ['Death Certificate application information',
                                   'Search for already registered death records',
                                   'Death Certificate correction services',
                                   'Non-availability of Death Certificate',
                                   'Late death registration information',
                                   'Application status information'],
                       'portal_name': 'Telangana MeeSeva - Death Certificate Services',
                       'portal_instructions': ['Visit the official Telangana MeeSeva portal and '
                                               'search for Death Certificate services. Choose GHMC '
                                               'for records within GHMC limits or CDMA for '
                                               'municipal records outside GHMC. For rural records, '
                                               'contact the relevant local registration authority. '
                                               'Death corrections, non-availability certificates '
                                               'and late registration are separate services. Check '
                                               'the applicable requirements before applying.'],
                       'official_url': 'https://ts.meeseva.telangana.gov.in/meeseva/home.htm'},
 'women-helpline': {'name': 'Women Helpline 181',
                    'description': 'Information about support and assistance available through the '
                                   'Telangana Women Helpline.',
                    'notice': 'Women Helpline 181 provides support and information to women in '
                              'distress. For emergencies, contact the appropriate emergency '
                              'service.',
                    'details': ['Women Helpline number: 181',
                                'Emergency assistance information',
                                "Information about women's support services",
                                'Guidance for women in distress',
                                'Official helpline contact details'],
                    'portal_name': 'Telangana Government Emergency Contacts',
                    'portal_instructions': ['Call 181 for Women Helpline support. Visit the '
                                            'official Telangana Government emergency contacts page '
                                            'for the listed helpline information.'],
                    'official_url': 'https://www.telangana.gov.in/contacts/emergency-contacts/'},
 'anganwadi': {'name': 'Telangana Anganwadi Services',
               'description': 'Information about Anganwadi centres, child nutrition, preschool '
                              'education and maternal and child welfare services.',
               'notice': 'The Telangana Women Development and Child Welfare Department provides '
                         'Anganwadi and child development services.',
               'details': ['Anganwadi centre information',
                           'Supplementary nutrition services',
                           'Preschool education information',
                           'Child health and development support',
                           'Arogya Lakshmi and Balamrutham information'],
               'portal_name': 'Telangana Women Development and Child Welfare Department',
               'portal_instructions': ['Visit the official Women Development and Child Welfare '
                                       'Department website to learn about Anganwadi centres and '
                                       'available services. Contact your local Anganwadi centre '
                                       'for information about services in your area.'],
               'official_url': 'https://wdcw.tg.nic.in/'},
 'child-protection': {'name': 'Child Protection and Child Helpline 1098',
                      'description': 'Information about child protection services and support for '
                                     'children in need of care and protection.',
                      'notice': 'Telangana lists Child Helpline 1098 for children in distress.',
                      'details': ['Child Helpline number: 1098',
                                  'Child protection information',
                                  'Support for children in need of care and protection',
                                  'Child welfare and rehabilitation information',
                                  'Integrated Child Protection Scheme information'],
                      'portal_name': 'Telangana Women Development and Child Welfare Department',
                      'portal_instructions': ['Call 1098 for Child Helpline assistance. Visit the '
                                              'official Telangana Women Development and Child '
                                              'Welfare Department website for information about '
                                              'child protection services.'],
                      'official_url': 'https://www.wdcw.tg.nic.in/icps_scheme'},
 'ration-card': {'name': 'Telangana Ration Card Services',
                 'description': 'Information about Telangana Food Security Cards, new ration cards '
                                'and existing ration card services.',
                 'notice': 'Ration Card services are provided through the Civil Supplies '
                           'Department and MeeSeva. Application availability and eligibility '
                           'should be confirmed with the relevant service centre.',
                 'details': ['New Food Security Card information',
                             'New Ration Card application information',
                             'Ration Card member addition',
                             'Ration Card member deletion',
                             'Ration Card corrections and modifications',
                             'Household head modifications',
                             'Ration Card transfer information',
                             'Application and service information'],
                 'portal_name': 'Telangana MeeSeva - Civil Supplies',
                 'portal_instructions': ['Visit the official Telangana MeeSeva service catalogue '
                                         'and look under Civil Supplies. Check the applicable '
                                         'service, eligibility conditions and required documents. '
                                         'Contact a MeeSeva centre or the relevant Civil Supplies '
                                         'office to confirm whether applications are currently '
                                         'being accepted.'],
                 'official_url': 'https://ts.meeseva.telangana.gov.in/TSDeptPortal/UserInterface/Services.html'},
 'bhu-bharati': {'name': 'Telangana Bhu Bharati Land Records',
                 'description': 'Information about Telangana land records, ownership details, '
                                'ROR-1B, e-Pahani and survey information.',
                 'notice': "Bhu Bharati is the Telangana Revenue Department's official land "
                           'records portal. Online information is provided for reference. Contact '
                           'the relevant Tahsildar or MRO office for official assistance when '
                           'required.',
                 'details': ['View ROR-1B land records',
                             'View e-Pahani information',
                             'Search land details',
                             'Land ownership history information',
                             'Survey number and land parcel map information',
                             'Land record correction information',
                             'Mutation and succession service information',
                             'Land grievance and appeal information'],
                 'portal_name': 'Telangana Bhu Bharati',
                 'portal_instructions': ['Visit the official Bhu Bharati portal. Open the relevant '
                                         'information or transactional service. Register or log in '
                                         'if required. Follow the portal instructions and check '
                                         'the required documents and applicable charges before '
                                         'submitting an application.'],
                 'official_url': 'https://bhubharati.telangana.gov.in/'},
 'indiramma-housing': {'name': 'Telangana Indiramma Indlu Housing Scheme',
                       'description': 'Information about Telangana Indiramma Indlu housing '
                                      'assistance for eligible homeless and economically weaker '
                                      'families.',
                       'notice': 'The Telangana Government provides housing assistance to eligible '
                                 'beneficiaries under the Indiramma Indlu Scheme. Eligibility, '
                                 'selection and assistance are subject to official government '
                                 'guidelines.',
                       'details': ['Indiramma Indlu scheme information',
                                   'Housing assistance information',
                                   'Eligibility conditions',
                                   'Beneficiary selection information',
                                   'Application status checking',
                                   'Required documents information',
                                   'Construction progress and assistance details',
                                   'Official scheme updates'],
                       'portal_name': 'Telangana Indiramma Indlu',
                       'portal_instructions': ['Visit the official Indiramma Indlu portal. Check '
                                               'the latest scheme guidelines, application search '
                                               'and beneficiary status options. Follow the '
                                               'official instructions and contact the relevant '
                                               'local government office for application '
                                               'assistance. Application availability may depend on '
                                               'current government notifications.'],
                       'official_url': 'https://indirammaindlu.telangana.gov.in/'},
 'tgnpdcl-electricity': {'name': 'TGNPDCL Electricity Services',
                         'description': 'Electricity bill payment, new connections and consumer '
                                        'services for Northern Telangana.',
                         'notice': 'TGNPDCL provides electricity distribution and consumer '
                                   'services in its service areas. Check your electricity bill to '
                                   'identify your distribution company.',
                         'details': ['Online electricity bill payment',
                                     'Know your electricity bill',
                                     'New electricity service connection',
                                     'Consumer complaints',
                                     'Power supply complaints',
                                     'Application status checking',
                                     'Name and load change services'],
                         'portal_name': 'TGNPDCL Official Portal',
                         'portal_instructions': ['Visit the official TGNPDCL portal to access '
                                                 'electricity bill payments, new connections and '
                                                 'consumer services. Consumers in other '
                                                 'distribution areas should use their respective '
                                                 'electricity company portal.'],
                         'official_url': 'https://www.tgnpdcl.com/'},
 'tgspdcl-electricity': {'name': 'TGSPDCL Electricity Services',
                         'description': 'Electricity bill payment, new connections and consumer '
                                        'services for Southern Telangana.',
                         'notice': 'TGSPDCL provides electricity distribution and consumer '
                                   'services in its service areas.',
                         'details': ['Online electricity bill payment',
                                     'Know your electricity bill',
                                     'New electricity connection',
                                     'Register electricity complaints',
                                     'Track complaint status',
                                     'Service requests',
                                     'Power supply information'],
                         'portal_name': 'TGSPDCL Official Portal',
                         'portal_instructions': ['Visit the official TGSPDCL portal to access '
                                                 'electricity bills, new connections and consumer '
                                                 'complaint services.'],
                         'official_url': 'https://tgspdclwebportal.tgsouthernpower.org/'},
 'mission-bhagiratha': {'name': 'Telangana Mission Bhagiratha',
                        'description': 'Information about rural drinking water supply and water '
                                       'connection services in Telangana.',
                        'notice': 'Mission Bhagiratha aims to provide safe drinking water to rural '
                                  'households in Telangana. Water connection availability and '
                                  'application procedures depend on official guidelines and local '
                                  'arrangements.',
                        'details': ['Rural drinking water supply information',
                                    'New water connection information',
                                    'Water supply complaints',
                                    'Connection charges information',
                                    'Water supply guidelines',
                                    'Contact information for local officials'],
                        'portal_name': 'Mission Bhagiratha',
                        'portal_instructions': ['Visit the official Mission Bhagiratha portal for '
                                                'water supply information. Contact the local '
                                                'Mission Bhagiratha office or Gram Panchayat for '
                                                'connection and complaint assistance.'],
                        'official_url': 'https://missionbhagiratha.telangana.gov.in/'},
 'ghmc-property-tax': {'name': 'GHMC Property Tax Services',
                       'description': 'Online property tax information and payment services '
                                      'provided by the Greater Hyderabad Municipal Corporation.',
                       'notice': 'This service is for properties covered by GHMC. Keep your PTIN '
                                 '(Property Tax Identification Number) ready.',
                       'details': ['Check property tax details',
                                   'View outstanding property tax dues',
                                   'Pay property tax online',
                                   'Property Tax Identification Number (PTIN) information',
                                   'Property tax self-assessment information',
                                   'Property tax payment receipt and status information'],
                       'portal_name': 'GHMC Official Portal',
                       'portal_instructions': ['Open the official GHMC website.',
                                               'Select Property Tax under e-Payment.',
                                               'Enter the required property details or PTIN.',
                                               'Check the displayed tax details and follow the '
                                               'official payment instructions.'],
                       'official_url': 'https://ghmc.gov.in/'},
 'social-welfare-schools': {'name': 'Telangana Social Welfare Residential Schools',
                            'description': 'Information about Telangana Social Welfare Residential '
                                           'Educational Institutions and student admissions.',
                            'notice': 'Admission notifications, eligibility and selection '
                                      'procedures are announced by the relevant society. Check '
                                      'current official notifications.',
                            'details': ['Residential school information',
                                        'Admission notifications and eligibility',
                                        'Entrance or selection process information',
                                        'School and society contact information'],
                            'portal_name': 'Telangana Social Welfare Residential Educational '
                                           'Institutions Society',
                            'portal_instructions': ['Open the official TSWREIS website.',
                                                    'Check the latest admission notification and '
                                                    'eligibility rules.',
                                                    'Follow the application instructions in the '
                                                    'current notification.'],
                            'official_url': 'https://tgswreis.telangana.gov.in/'},
 'minority-welfare-education': {'name': 'Telangana Minority Education and Scholarship Information',
                                'description': 'Information about education concessions, '
                                               'scholarships and educational support listed by the '
                                               'Telangana Minorities Welfare Department.',
                                'notice': 'Scholarship schemes and application windows depend on '
                                          'current state and central government notifications.',
                                'details': ['Pre-matric and post-matric scholarship information',
                                            'Merit-cum-Means scholarship information',
                                            'Hostel and educational support information',
                                            'Department notifications and contacts'],
                                'portal_name': 'Telangana Minorities Welfare Department',
                                'portal_instructions': ['Visit the official Telangana Minorities '
                                                        'Welfare Department page.',
                                                        'Review the current scholarship and '
                                                        'education scheme details.',
                                                        'Use the linked official application '
                                                        'portal where a scheme notification '
                                                        'directs you.'],
                                'official_url': 'https://www.telangana.gov.in/departments/minorities-welfare/'},
 'task-skill-development': {'name': 'Telangana Skill Development and TASK',
                            'description': 'Information about skill development, training and '
                                           'industry-readiness initiatives in Telangana.',
                            'notice': 'Course availability, eligibility and registration depend on '
                                      'current programme announcements.',
                            'details': ['Skill development programme information',
                                        'Training and employability initiatives',
                                        'Industry and academic collaboration information',
                                        'Programme updates'],
                            'portal_name': 'Telangana Academy for Skill and Knowledge',
                            'portal_instructions': ['Visit the official TASK website.',
                                                    'Review available programmes and eligibility.',
                                                    'Follow the registration instructions '
                                                    'published for each programme.'],
                            'official_url': 'https://task.telangana.gov.in/'},
 'industries-employment': {'name': 'Telangana Industries and Commerce Department',
                           'description': 'Information about state industrial development '
                                          'initiatives, entrepreneurship support and department '
                                          'services.',
                           'notice': 'This is a department information page; individual '
                                     'recruitment and scheme applications are subject to separate '
                                     'notifications.',
                           'details': ['Department and organisation information',
                                       'Industrial development initiatives',
                                       'Entrepreneurship support information',
                                       'Official notifications and contacts'],
                           'portal_name': 'Telangana Industries and Commerce Department',
                           'portal_instructions': ['Visit the official department website.',
                                                   'Open the relevant scheme or service section.',
                                                   'Check current guidelines and contact details '
                                                   'before applying.'],
                           'official_url': 'https://industries.telangana.gov.in'},
 'agriculture-department': {'name': 'Telangana Agriculture Department Services',
                            'description': 'Information about agriculture department programmes, '
                                           'farmer support and agricultural services.',
                            'notice': 'Scheme eligibility, application dates and benefits are '
                                      'governed by current official guidelines.',
                            'details': ['Agriculture department information',
                                        'Farmer welfare programme updates',
                                        'Crop and input advisory information',
                                        'Department contacts and notifications'],
                            'portal_name': 'Telangana Agriculture Department',
                            'portal_instructions': ['Visit the official Agriculture Department '
                                                    'website.',
                                                    'Check current scheme notifications and farmer '
                                                    'advisories.',
                                                    'Contact the local Agriculture Officer for '
                                                    'service-specific guidance.'],
                            'official_url': 'https://agri.telangana.gov.in/'},
 'agriculture-licences': {'name': 'Telangana Online Licence Management for Agriculture',
                          'description': 'Online information and application access for '
                                         'agricultural licences listed by the Telangana '
                                         'Agriculture Department.',
                          'notice': 'Available licence types and application requirements are '
                                    'shown on the official portal.',
                          'details': ['Agricultural licence information',
                                      'Online application access',
                                      'Application requirements',
                                      'Licence-related updates'],
                          'portal_name': 'Online Licence Management System for Agriculture',
                          'portal_instructions': ['Open the official agriculture licence portal.',
                                                  'Choose the relevant licence service.',
                                                  'Review the required details and documents '
                                                  'before submitting.'],
                          'official_url': 'https://agriolms.telangana.gov.in/Default.aspx'},
 'health-department': {'name': 'Telangana Health Department Services',
                       'description': 'Information about public health programmes and services of '
                                      'the Telangana Health, Medical and Family Welfare '
                                      'Department.',
                       'notice': 'Hospital services, programme availability and eligibility should '
                                 'be confirmed with the relevant health facility or department.',
                       'details': ['Public health programme information',
                                   'Government health facility information',
                                   'Department notifications',
                                   'Health department contacts'],
                       'portal_name': 'Telangana Health, Medical and Family Welfare Department',
                       'portal_instructions': ['Visit the official Health Department website.',
                                               'Choose the relevant programme or service section.',
                                               'Contact the listed government facility for current '
                                               'service details.'],
                       'official_url': 'https://chfw.telangana.gov.in/home.do'},
 'women-child-department': {'name': 'Telangana Women and Child Welfare Department',
                            'description': 'Information about women and child development '
                                           'programmes administered by the Telangana department.',
                            'notice': 'Programme eligibility and application procedures depend on '
                                      'official notifications and local department arrangements.',
                            'details': ['Women welfare programme information',
                                        'Child development and nutrition programmes',
                                        'Department schemes and notifications',
                                        'District and local office information'],
                            'portal_name': 'Telangana Women Development and Child Welfare '
                                           'Department',
                            'portal_instructions': ['Visit the official department website.',
                                                    'Review the programme information and latest '
                                                    'notices.',
                                                    'Contact the local department office or '
                                                    'Anganwadi centre for local services.'],
                            'official_url': 'https://wdcw.tg.nic.in/'},
 'civil-supplies': {'name': 'Telangana Civil Supplies Department Information',
                    'description': 'Information about food security, public distribution and Civil '
                                   'Supplies Department services.',
                    'notice': 'Ration card applications and modifications are subject to current '
                              'eligibility and government instructions.',
                    'details': ['Public distribution system information',
                                'Food Security Card information',
                                'Civil Supplies department updates',
                                'Citizen service guidance'],
                    'portal_name': 'Telangana Civil Supplies / MeeSeva',
                    'portal_instructions': ['Visit the Telangana MeeSeva service catalogue.',
                                            'Look under Civil Supplies for the relevant service.',
                                            'Confirm current requirements with MeeSeva or the '
                                            'Civil Supplies office.'],
                    'official_url': 'https://ts.meeseva.telangana.gov.in/TSDeptPortal/UserInterface/Services.html'},
 'registration-encumbrance': {'name': 'Telangana Encumbrance Certificate Information',
                              'description': 'Information about Encumbrance Certificate services '
                                             'through the Telangana Registration and Stamps '
                                             'Department.',
                              'notice': 'An Encumbrance Certificate is a registration record '
                                        'search; verify property details and the applicable period '
                                        'carefully.',
                              'details': ['Encumbrance Certificate service information',
                                          'Property registration record search',
                                          'Application and document guidance',
                                          'Registration Department information'],
                              'portal_name': 'Telangana Registration and Stamps Department',
                              'portal_instructions': ['Visit the official Telangana State Services '
                                                      'page or Registration and Stamps Department '
                                                      'portal.',
                                                      'Choose the Encumbrance Certificate service.',
                                                      'Follow the current official instructions '
                                                      'and verify property details.'],
                              'official_url': 'https://www.telangana.gov.in/services/state-services/'},
 'driving-licence': {'name': 'Telangana Driving Licence Services',
                     'description': 'Information and online access for learner and driving licence '
                                    'services in Telangana.',
                     'notice': 'Licence eligibility, fees, documents and appointment availability '
                               'are controlled by the Transport Department.',
                     'details': ['Learner licence services',
                                 'Driving licence application and renewal',
                                 'Duplicate and address change services',
                                 'Driving test slot booking and application status'],
                     'portal_name': 'Telangana Transport Department Online Services',
                     'portal_instructions': ['Open the official Telangana Transport online '
                                             'services portal.',
                                             'Choose the required licence transaction.',
                                             'Follow the instructions for forms, fees and slot '
                                             'booking.'],
                     'official_url': 'https://tgtransport.net/TGCFSTONLINE/OnlineTransactions/LicenseOnline.aspx'},
 'vehicle-registration': {'name': 'Telangana Vehicle Registration Services',
                          'description': 'Information and online access for vehicle registration '
                                         'and related services in Telangana.',
                          'notice': 'Vehicle-related transactions depend on vehicle class, '
                                    'documents and the concerned RTA office.',
                          'details': ['New vehicle registration information',
                                      'Ownership transfer',
                                      'Address change and duplicate registration',
                                      'Registration application status'],
                          'portal_name': 'Telangana Transport Department',
                          'portal_instructions': ['Visit the official Telangana Transport '
                                                  'Department portal.',
                                                  'Choose the relevant vehicle registration '
                                                  'service.',
                                                  'Check the required documents and transaction '
                                                  'instructions.'],
                          'official_url': 'https://transport.telangana.gov.in/'},
 'housing-board': {'name': 'Telangana Housing Board Information',
                   'description': 'Information about Telangana Housing Board projects, schemes and '
                                  'citizen updates.',
                   'notice': 'Project availability, allotments and application windows are subject '
                             'to official notifications.',
                   'details': ['Housing Board project information',
                               'Scheme and allotment notifications',
                               'Citizen information and contacts',
                               'Official updates'],
                   'portal_name': 'Telangana Housing Board',
                   'portal_instructions': ['Visit the official Telangana Housing Board website.',
                                           'Check current project and allotment notifications.',
                                           'Follow only the application instructions published by '
                                           'the Housing Board.'],
                   'official_url': 'https://tshousing.cgg.gov.in/'},
 'ghmc-trade-licence': {'name': 'GHMC Trade Licence Services',
                        'description': 'Information about applying for and paying for a trade '
                                       'licence within GHMC limits.',
                        'notice': 'Trade licence requirements, fees and approvals are determined '
                                  'by GHMC and the applicable rules.',
                        'details': ['Apply for a new trade licence',
                                    'Trade licence payment information',
                                    'Renewal and licence details',
                                    'Application and document guidance'],
                        'portal_name': 'Greater Hyderabad Municipal Corporation',
                        'portal_instructions': ['Open the official GHMC website.',
                                                'Choose Trade Licence under e-Payment or e-Request '
                                                'as applicable.',
                                                'Review the required documents, fee and current '
                                                'application instructions.'],
                        'official_url': 'https://ghmc.gov.in/'},
 'ghmc-building-permission': {'name': 'GHMC Building Permission Information',
                              'description': 'Information about building permission and '
                                             'development approval services in Hyderabad.',
                              'notice': 'The applicable authority and approval route depend on the '
                                        'property location, building type and size.',
                              'details': ['Building permission information',
                                          'Application and approval process',
                                          'Occupancy certificate information',
                                          'Building application status guidance'],
                              'portal_name': 'Telangana BuildNow',
'portal_instructions': [
    'Open the official Telangana BuildNow portal.',
    'Select the applicable building permission service.',
    'Review eligibility, required documents and approval steps.'
],
'official_url': 'https://buildnow.telangana.gov.in'
 },
 'ghmc-grievance': {'name': 'GHMC Citizen Grievance Services',
                    'description': 'Information about lodging and following up on civic grievances '
                                   'within GHMC limits.',
                    'notice': 'Use the official GHMC grievance channel for complaints and retain '
                              'the acknowledgement or reference number.',
                    'details': ['Lodge civic grievances',
                                'Grievance acknowledgement information',
                                'Complaint follow-up guidance',
                                'GHMC citizen service information'],
                    'portal_name': 'Greater Hyderabad Municipal Corporation',
                    'portal_instructions': ['Visit the official GHMC website.',
                                            'Choose Lodge Grievance under e-Complaints.',
                                            'Submit the details and retain the complaint reference '
                                            'for follow-up.'],
                    'official_url': 'https://ghmc.gov.in/'},
 'ghmc-vacant-land-tax': {'name': 'GHMC Vacant Land Tax Services',
                          'description': 'Information about vacant land tax services listed by the '
                                         'Greater Hyderabad Municipal Corporation.',
                          'notice': 'This service applies only where GHMC tax rules and property '
                                    'records make it applicable.',
                          'details': ['Vacant land tax information',
                                      'Tax payment access',
                                      'Property and assessment details',
                                      'Payment guidance'],
                          'portal_name': 'Greater Hyderabad Municipal Corporation',
                          'portal_instructions': ['Open the official GHMC website.',
                                                  'Choose Vacant Land Tax under e-Payment.',
                                                  'Check the property details and follow the '
                                                  'official payment instructions.'],
                          'official_url': 'https://ghmc.gov.in/'},
 'police-online-complaint': {'name': 'Telangana Police Online Complaint Information',
                             'description': 'Information about online complaint and citizen '
                                            'services provided by Telangana Police.',
                             'notice': 'For immediate danger or emergencies, contact the '
                                       'appropriate emergency number rather than relying on an '
                                       'online form.',
                             'details': ['Online complaint registration information',
                                         'Citizen service guidance',
                                         'Complaint follow-up information',
                                         'Police station contact guidance'],
                             'portal_name': 'Telangana Police',
                             'portal_instructions': ['Visit the official Telangana Police website '
                                                     'or Telangana State Services page.',
                                                     'Choose the relevant citizen service.',
                                                     'Follow the instructions and retain any '
                                                     'acknowledgement number.'],
                             'official_url': 'https://www.tspolice.gov.in/'},
 'police-missing-person': {'name': 'Telangana Missing Person Services',
                           'description': 'Information about missing person registration and '
                                          'related police citizen services.',
                        'notice': 'If a person is missing, contact the nearest police station promptly. For immediate danger, call 112.',
                           'details': ['Missing person registration information',
                                       'Police assistance guidance',
                                       'Related citizen service information',
                                       'Emergency contact guidance'],
                           'portal_name': 'Telangana State Services',
                           'portal_instructions': ['Open the official Telangana State Services '
                                                   'page.',
                                                   'Choose Missing Person Registration under '
                                                   'Police Department services.',
                                                   'Follow the official instructions or contact '
                                                   'the nearest police station.'],
                           'official_url': 'https://www.telangana.gov.in/services/state-services/'},
 'police-fir-copy': {'name': 'Telangana FIR Copy Request Information',
                     'description': 'Information about requesting a copy of an FIR through the '
                                    'listed Telangana Police citizen services.',
                     'notice': 'Access to FIR records is subject to applicable law and police '
                               'procedures.',
                     'details': ['FIR copy request information',
                                 'Police citizen service guidance',
                                 'Required reference details',
                                 'Follow-up information'],
                     'portal_name': 'Telangana State Services',
                     'portal_instructions': ['Visit the official Telangana State Services page.',
                                             'Choose Request for FIR Copy under Police Department '
                                             'services.',
                                             'Follow the current instructions and eligibility '
                                             'conditions.'],
                     'official_url': 'https://www.telangana.gov.in/services/state-services/'},
 'labour-department': {'name': 'Telangana Labour Department Services',
                       'description': 'Information about labour welfare, worker protections and '
                                      'department services in Telangana.',
                       'notice': 'Registration, benefits and grievance procedures depend on the '
                                 'relevant labour law and current department rules.',
                       'details': ['Labour department information',
                                   'Worker welfare scheme information',
                                   'Labour law and service guidance',
                                   'Department contacts and notifications'],
                       'portal_name': 'Telangana Labour Department',
                       'portal_instructions': ['Visit the official Telangana State Portal and open '
                                               'the Labour Department section.',
                                               'Identify the relevant worker service or scheme.',
                                               'Confirm eligibility and documents with the '
                                               'department before applying.'],
                       'official_url': 'https://labour.telangana.gov.in/'},
 'building-workers-welfare': {'name': 'Telangana Building and Other Construction Workers Welfare '
                                      'Information',
                              'description': 'Information about welfare services for eligible '
                                             'building and other construction workers.',
                              'notice': 'Registration and welfare benefits are subject to the '
                                        'applicable Board rules and eligibility requirements.',
                              'details': ['Construction worker welfare information',
                                          'Worker registration guidance',
                                          'Welfare benefit information',
                                          'Required documents and department contacts'],
                              'portal_name': 'Telangana Labour Department',
                              'portal_instructions': ['Visit the official Telangana government '
                                                      'portal and open the Labour Department '
                                                      'section.',
                                                      'Check the current Building and Other '
                                                      'Construction Workers Welfare Board '
                                                      'instructions.',
                                                      'Confirm registration and benefit '
                                                      'requirements with the relevant office.'],
                              'official_url': 'https://tbocwwb.telangana.gov.in/'},
 'ts-ipass': {'name': 'Telangana TS-iPASS Business Approvals',
              'description': 'Information about the Telangana industrial project approval and '
                             'self-certification system.',
              'notice': 'Approvals and clearances depend on the business activity, project and '
                        'applicable departmental requirements.',
              'details': ['Industrial project approval information',
                          'Single-window clearance guidance',
                          'Trade licence process information',
                          'Application tracking and official updates'],
              'portal_name': 'Telangana TS-iPASS',
              'portal_instructions': ['Visit the official TS-iPASS portal.',
                                      'Review the approval or clearance required for your project.',
                                      'Use the portal checklist and follow the application '
                                      'process.'],
              'official_url': 'https://ipass.telangana.gov.in/'},
 'startup-telangana': {'name': 'Startup Telangana Information',
                       'description': 'Information about startup support, entrepreneurship '
                                      'initiatives and innovation programmes in Telangana.',
                       'notice': 'Programme availability, eligibility and benefits are subject to '
                                 'current official announcements.',
                       'details': ['Startup ecosystem information',
                                   'Entrepreneurship support initiatives',
                                   'Incubation and programme updates',
                                   'Official contacts and resources'],
                       'portal_name': 'Startup Telangana',
                       'portal_instructions': ['Visit the official Telangana Industries and '
                                               'Commerce website.',
                                               'Check current startup and entrepreneurship '
                                               'programme information.',
                                               'Follow the programme-specific instructions '
                                               'published by the department.'],
                       'official_url': 'https://startup.telangana.gov.in/'},
 'sc-welfare': {'name': 'Telangana Scheduled Caste Welfare Information',
                'description': 'Information about Scheduled Caste development, education and '
                               'welfare programmes in Telangana.',
                'notice': 'Eligibility and application procedures vary by scheme and are governed '
                          'by current department guidelines.',
                'details': ['SC welfare scheme information',
                            'Educational support and residential institutions',
                            'Economic development programmes',
                            'Department contacts and notifications'],
                'portal_name': 'Telangana Social Welfare Department',
                'portal_instructions': ['Visit the official Telangana Social Welfare Department '
                                        'page.',
                                        'Review the relevant scheme or institution details.',
                                        'Check current eligibility and application instructions.'],
                'official_url': 'https://www.telangana.gov.in/Departments/Social-Welfare/'},
 'bc-welfare': {'name': 'Telangana Backward Classes Welfare Information',
                'description': 'Information about Backward Classes welfare programmes and '
                               'department services in Telangana.',
                'notice': 'Scheme availability and eligibility are subject to current government '
                          'guidelines.',
                'details': ['BC welfare scheme information',
                            'Education and hostel support information',
                            'Economic support programme information',
                            'Department contacts and notifications'],
                'portal_name': 'Telangana Backward Classes Welfare Department',
                'portal_instructions': ['Visit the official Telangana Backward Classes Welfare '
                                        'Department page.',
                                        'Check the relevant welfare programme and current '
                                        'eligibility.',
                                        "Follow the department's official application "
                                        'instructions.'],
                'official_url': 'https://www.telangana.gov.in/Departments/Backward-Classes-Welfare/'},
 'minority-welfare': {'name': 'Telangana Minorities Welfare Services',
                      'description': 'Information about educational, social and economic '
                                     'development programmes for minority communities.',
                      'notice': 'Benefits and application windows depend on the current scheme '
                                'guidelines and official notifications.',
                      'details': ['Minority education support information',
                                  'Shaadi Mubarak scheme information',
                                  'Training and employment support',
                                  'Economic assistance programme information'],
                      'portal_name': 'Telangana Minorities Welfare Department',
                      'portal_instructions': ['Visit the official Telangana Minorities Welfare '
                                              'Department page.',
                                              'Review the relevant scheme details and eligibility.',
                                              'Use the application route specified in the current '
                                              'official notification.'],
                      'official_url': 'https://www.telangana.gov.in/departments/minorities-welfare/'},
 'meeseva-services': {'name': 'Telangana MeeSeva Citizen Services',
                      'description': 'Information about citizen services available through '
                                     'Telangana MeeSeva centres and online portal.',
                      'notice': 'The available service list, fees and required documents can '
                                'change. Check the official catalogue before applying.',
                      'details': ['Revenue and certificate services',
                                  'Civil Supplies services',
                                  'Local body and other department services',
                                  'Application status and service guidance'],
                      'portal_name': 'Telangana MeeSeva',
                      'portal_instructions': ['Visit the official MeeSeva portal.',
                                              'Search the service catalogue for the required '
                                              'department and service.',
                     
                                              'Check the current fee, documents and application '
                                              'instructions.'],
                      'official_url': 'https://ts.meeseva.telangana.gov.in/'},
 'rti-information': {'name': 'Telangana Right to Information (RTI) Information',
                     'description': 'General information about accessing government information '
                                    'under the Right to Information framework.',
                     'notice': 'Submit RTI requests to the appropriate public authority and follow '
                               'the applicable RTI rules and fees.',
                     'details': ['RTI application information',
                                 'Public authority identification guidance',
                                 'Application and appeal information',
                                 'Government department contact guidance'],
                     'portal_name': 'Telangana State Portal',
                     'portal_instructions': ['Visit the official Telangana State Portal.',
                                             'Identify the public authority holding the '
                                             'information.',
                                             'Follow the applicable RTI Act and department '
                                             'instructions for submitting a request.'],
                     'official_url': 'https://www.telangana.gov.in/'},
 'old-age-pension': {'name': 'Telangana Old Age Pension Information',
                     'description': 'Information about old age pension support under Telangana '
                                    'social security pension services.',
                     'notice': 'Eligibility, required documents and benefit amounts are governed '
                               'by current Telangana Government guidelines. Confirm the applicable '
                               'rules with the official department.',
                     'details': ['Old age pension scheme information',
                                 'Eligibility and required documents information',
                                 'Application and verification guidance',
                                 'Pension status and official updates'],
                     'portal_name': 'Telangana Cheyutha',
                     'portal_instructions': ['Visit the official Telangana Cheyutha portal.',
                                             'Review the current pension scheme guidelines.',
                                             'Contact the relevant local government office if you '
                                             'need help confirming eligibility or application '
                                             'status.'],
                     'official_url': 'https://www.cheyutha.telangana.gov.in/'},
 'widow-pension': {'name': 'Telangana Widow Pension Information',
                   'description': 'Information about widow pension support under Telangana social '
                                  'security pension services.',
                   'notice': 'Eligibility, required documents and benefit amounts are governed by '
                             'current Telangana Government guidelines. Confirm the applicable '
                             'rules with the official department.',
                   'details': ['Widow pension scheme information',
                               'Eligibility and required documents information',
                               'Application and verification guidance',
                               'Pension status and official updates'],
                   'portal_name': 'Telangana Cheyutha',
                   'portal_instructions': ['Visit the official Telangana Cheyutha portal.',
                                           'Review the current pension scheme guidelines.',
                                           'Contact the relevant local government office if you '
                                           'need help confirming eligibility or application '
                                           'status.'],
                   'official_url': 'https://www.cheyutha.telangana.gov.in/'},
 'disability-pension': {'name': 'Telangana Disability Pension Information',
                        'description': 'Information about disability pension support under '
                                       'Telangana social security pension services.',
                        'notice': 'Eligibility, required documents and benefit amounts are '
                                  'governed by current Telangana Government guidelines. Confirm '
                                  'the applicable rules with the official department.',
                        'details': ['Disability pension scheme information',
                                    'Eligibility and required documents information',
                                    'Application and verification guidance',
                                    'Pension status and official updates'],
                        'portal_name': 'Telangana Cheyutha',
                        'portal_instructions': ['Visit the official Telangana Cheyutha portal.',
                                                'Review the current pension scheme guidelines.',
                                                'Contact the relevant local government office if '
                                                'you need help confirming eligibility or '
                                                'application status.'],
                        'official_url': 'https://www.cheyutha.telangana.gov.in/'}}


categories = {'education': {'name': 'Education',
               'description': 'Student scholarships and education-related services.',
               'services': ['scholarship', 'social-welfare-schools', 'minority-welfare-education']},
 'employment': {'name': 'Employment',
                'description': 'Government jobs and recruitment information.',
                'services': ['jobs', 'task-skill-development', 'industries-employment']},
 'pension': {'name': 'Pension',
             'description': 'Pension and social security services.',
             'services': ['pension', 'old-age-pension', 'widow-pension', 'disability-pension']},
 'agriculture': {'name': 'Agriculture',
                 'description': 'Farmer welfare and agriculture-related services.',
                 'services': ['farmer', 'agriculture-department', 'agriculture-licences']},
 'healthcare': {'name': 'Healthcare',
                'description': 'Healthcare and medical support services.',
                'services': ['health', 'health-department']},
 'women-child': {'name': 'Women and Child Welfare',
                 'description': 'Women and child development services.',
                 'services': ['women-helpline',
                              'anganwadi',
                              'child-protection',
                              'women-child-department']},
 'certificates': {'name': 'Certificates',
                  'description': 'Government certificates and MeeSeva services.',
                  'services': ['income-certificate',
                               'caste-certificate',
                               'residence-certificate',
                               'birth-certificate',
                               'death-certificate']},
 'food': {'name': 'Food and Civil Supplies',
          'description': 'Ration card and food supply services.',
          'services': ['ration-card', 'civil-supplies']},
 'land': {'name': 'Land and Revenue',
          'description': 'Land records and revenue-related services.',
          'services': ['bhu-bharati', 'registration-encumbrance']},
 'transport': {'name': 'Transport',
               'description': 'Public transport and bus pass services.',
               'services': ['bus-pass', 'driving-licence', 'vehicle-registration']},
 'housing': {'name': 'Housing',
             'description': 'Housing-related government services.',
             'services': ['indiramma-housing', 'housing-board']},
 'electricity-water': {'name': 'Electricity and Water',
                       'description': 'Electricity supply, bill payment and drinking water '
                                      'services.',
                       'services': ['tgnpdcl-electricity',
                                    'tgspdcl-electricity',
                                    'mission-bhagiratha']},
 'municipal': {'name': 'Municipal Services',
               'description': 'Municipal and local body services.',
               'services': ['ghmc-property-tax',
                            'ghmc-trade-licence',
                            'ghmc-building-permission',
                            'ghmc-grievance',
                            'ghmc-vacant-land-tax']},
 'police': {'name': 'Police Services',
            'description': 'Police and public safety services.',
            'services': ['police-online-complaint', 'police-missing-person', 'police-fir-copy']},
 'labour': {'name': 'Labour Services',
            'description': 'Labour welfare and worker services.',
            'services': ['labour-department', 'building-workers-welfare']},
 'business': {'name': 'Business Services',
              'description': 'Business registration and support services.',
              'services': ['ts-ipass', 'startup-telangana']},
 'social-welfare': {'name': 'Social Welfare',
                    'description': 'Social welfare and community support services.',
                    'services': ['sc-welfare', 'bc-welfare', 'minority-welfare']},
 'other': {'name': 'Other Services',
           'description': 'Other Telangana government services.',
           'services': ['meeseva-services', 'rti-information']}}


# ============================================================
# HOME PAGE
# ============================================================
initialize_database(categories, services)
@app.route("/")
def home():
    database_categories = {
        category["category_key"]: category
        for category in get_all_categories()
    }

    return render_template(
        "index.html",
        categories=database_categories
    )
# ============================================================
# SEARCH SERVICES
# ============================================================


@app.route("/search")
def search():
    search_text = (
        request.args.get("query", "").strip()
        or request.args.get("q", "").strip()
        or request.args.get("search", "").strip()
    )

    results = []
    search_lower = " ".join(search_text.lower().split())

    if search_lower:

        # 1. Search categories and services using SQLite.
        results = search_database(search_lower)

        # 2. Alternative keywords.
        keyword_map = {
            "student": ["scholarship", "social-welfare-schools", "minority-welfare-education"],
            "students": ["scholarship", "social-welfare-schools", "minority-welfare-education"],
            "epass": ["scholarship"],
            "education": ["scholarship", "social-welfare-schools", "minority-welfare-education"],
            "school": ["social-welfare-schools"],
            "skill": ["task-skill-development"],
            "training": ["task-skill-development"],
            "job": ["jobs", "task-skill-development"],
            "employment": ["jobs", "task-skill-development"],
            "tgpsc": ["jobs"],
            "bus": ["bus-pass"],
            "bus pass": ["bus-pass"],
            "rtc": ["bus-pass"],
            "driving": ["driving-licence"],
            "licence": ["driving-licence", "ghmc-trade-licence"],
            "license": ["driving-licence", "ghmc-trade-licence"],
            "vehicle": ["vehicle-registration"],
            "registration": ["vehicle-registration", "registration-encumbrance"],
            "pension": ["pension", "old-age-pension", "widow-pension", "disability-pension"],
            "farmer": ["farmer", "agriculture-department"],
            "agriculture": ["farmer", "agriculture-department", "agriculture-licences"],
            "rythu": ["farmer"],
            "hospital": ["health", "health-department"],
            "health": ["health", "health-department"],
            "medical": ["health", "health-department"],
            "aarogyasri": ["health"],
            "income": ["income-certificate"],
            "caste": ["caste-certificate"],
            "residence": ["residence-certificate"],
            "birth": ["birth-certificate"],
            "death": ["death-certificate"],
            "women": ["women-helpline", "women-child-department"],
            "child": ["child-protection", "anganwadi"],
            "anganwadi": ["anganwadi"],
            "ration": ["ration-card", "civil-supplies"],
            "food": ["ration-card", "civil-supplies"],
            "land": ["bhu-bharati"],
            "pahani": ["bhu-bharati"],
            "property tax": ["ghmc-property-tax"],
            "ptin": ["ghmc-property-tax"],
            "trade licence": ["ghmc-trade-licence"],
            "trade license": ["ghmc-trade-licence"],
            "building permission": ["ghmc-building-permission"],
            "grievance": ["ghmc-grievance"],
            "complaint": ["ghmc-grievance", "police-online-complaint"],
            "police": ["police-online-complaint", "police-missing-person", "police-fir-copy"],
            "fir": ["police-fir-copy"],
            "missing person": ["police-missing-person"],
            "labour": ["labour-department", "building-workers-welfare"],
            "worker": ["labour-department", "building-workers-welfare"],
            "business": ["ts-ipass", "startup-telangana"],
            "startup": ["startup-telangana"],
            "msme": ["ts-ipass"],
            "sc welfare": ["sc-welfare"],
            "bc welfare": ["bc-welfare"],
            "minority": ["minority-welfare", "minority-welfare-education"],
            "rti": ["rti-information"],
            "meeseva": ["meeseva-services"],
        }

        # 3. Add alternative keyword results.
        if search_lower in keyword_map:
            for key in keyword_map[search_lower]:

                service = get_service_data(key)

                if service and not any(
                    item["key"] == key and item["type"] == "service"
                    for item in results
                ):
                    results.append({
                        "key": key,
                        "name": service["name"],
                        "description": service["description"],
                        "type": "service"
                    })

    return render_template(
        "results.html",
        results=results,
        search_text=search_text
    )

# ============================================================
# CATEGORY PAGE
# ============================================================
@app.route("/category/<category_key>")
def category(category_key):

    selected_category, category_services = get_category_data(category_key)

    if not selected_category:
        return "Category not found", 404

    return render_template(
        "category.html",
        category=selected_category,
        category_services=category_services
    )


# ============================================================
# SERVICE DETAILS PAGE
# ============================================================

@app.route("/details/<service_key>")
def details(service_key):

    service = get_service_data(service_key)

    if not service:
        return "Service not found", 404

    return render_template(
        "details.html",
        service=service
    )

@app.route("/add-favorite/<service_key>", methods=["POST"])
def add_favorite_route(service_key):

    if "user_id" not in session:
        flash("Please log in to save favourite services.", "error")
        return redirect(url_for("login"))

    service = get_service_data(service_key)

    if not service:
        return "Service not found", 404

    added = add_favorite(
        session["user_id"],
        service_key
    )

    if added:
        flash("Service added to your favourites!", "success")
    else:
        flash("This service is already in your favourites.", "info")

    return redirect(url_for("details", service_key=service_key))

@app.route("/remove-favorite/<service_key>", methods=["POST"])
def remove_favorite_route(service_key):

    if "user_id" not in session:
        return redirect(url_for("login"))

    remove_favorite(
        session["user_id"],
        service_key
    )

    flash("Service removed from your favourites.", "success")

    return redirect(url_for("profile"))

# ============================================================
# RUN APPLICATION
# ============================================================

if __name__ == "__main__":
    app.run(debug=True)

# ============================================================
# USER REGISTRATION
# ============================================================

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        if len(username) < 3 or len(username) > 50:
            flash("Username must be between 3 and 50 characters.", "error")
            return render_template("register.html")

        if len(email) > 254:
            flash("Email address is too long.", "error")
            return render_template("register.html")

        if len(password) < 8:
            flash("Password must contain at least 8 characters.", "error")
            return render_template("register.html")

        if password != confirm_password:
            flash("Passwords do not match.", "error")
            return render_template("register.html")

        password_hash = generate_password_hash(password)

        if add_user(username, email, password_hash):
            flash("Registration successful! Please log in.", "success")
            return redirect(url_for("login"))

        flash("This email address is already registered.", "error")
        return render_template("register.html")

    return render_template("register.html")

# ============================================================
# USER LOGIN
# ============================================================
@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        user = get_user_by_email(email)

        if user and check_password_hash(user["password_hash"], password):

            session.clear()

            session["user_id"] = user["id"]
            session["username"] = user["username"]
            session["email"] = user["email"]

            flash("Login successful!", "success")
            return redirect(url_for("profile"))

        flash("Invalid email or password.", "error")

    return render_template("login.html")

        

    

@app.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():

    if request.method == "POST":

        email = request.form.get("email", "").strip().lower()
        user = get_user_by_email(email)

        if user:
            token = secrets.token_urlsafe(32)

            token_hash = hashlib.sha256(
                token.encode()
            ).hexdigest()

            expires_at = (
                datetime.now(timezone.utc) +
                timedelta(minutes=15)
            ).isoformat()

            save_password_reset(email, token_hash, expires_at)

            reset_link = url_for(
                "reset_password",
                token=token,
                _external=True
            )

            print("\nPASSWORD RESET LINK (LOCAL TESTING):")
            print(reset_link)
            print()

        flash(
            "If your email is registered, a password reset link has been generated. Check the terminal for local testing.",
            "success"
        )

        return redirect(url_for("login"))

    return render_template("forgot_password.html")


@app.route("/reset-password/<token>", methods=["GET", "POST"])
def reset_password(token):

    token_hash = hashlib.sha256(token.encode()).hexdigest()
    reset_data = get_password_reset(token_hash)

    if not reset_data:
        flash("Invalid or already used reset link.", "error")
        return redirect(url_for("forgot_password"))

    expires_at = datetime.fromisoformat(reset_data["expires_at"])

    if expires_at <= datetime.now(timezone.utc):
        delete_password_reset(token_hash)
        flash("Reset link expired. Please request a new one.", "error")
        return redirect(url_for("forgot_password"))

    if request.method == "POST":

        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        if len(password) < 8:
            flash("Password must contain at least 8 characters.", "error")

        elif password != confirm_password:
            flash("Passwords do not match.", "error")

        else:
            password_hash = generate_password_hash(password)

            if update_user_password(reset_data["email"], password_hash):
                delete_password_reset(token_hash)
                flash("Password reset successful. Please log in.", "success")
                return redirect(url_for("login"))

            flash("Unable to reset password. Please try again.", "error")

    return render_template("reset_password.html")


@app.route("/profile")
def profile():

    if "user_id" not in session:
        return redirect(url_for("login"))

    favorites = get_user_favorites(session["user_id"])

    return render_template(
        "profile.html",
        username=session.get("username"),
        email=session.get("email"),
        favorites=favorites
    )

# ============================================================
# USER LOGOUT
# ============================================================

@app.route("/logout", methods=["POST"])
def logout():
    session.clear()
    flash("You have been logged out successfully.", "success")
    return redirect(url_for("home"))
