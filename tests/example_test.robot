*** Settings ***
Library    SeleniumLibrary
Library    OperatingSystem

*** Variables ***
${PROFILE_DIR}    ${EMPTY}

*** Test Cases ***
Open Google
    ${PROFILE_DIR}=    Evaluate    __import__('tempfile').mkdtemp()
    ${chrome_options}=    Evaluate    sys.modules['selenium.webdriver'].ChromeOptions()    sys
    Call Method    ${chrome_options}    add_argument    --headless
    Call Method    ${chrome_options}    add_argument    --no-sandbox
    Call Method    ${chrome_options}    add_argument    --disable-dev-shm-usage
    Call Method    ${chrome_options}    add_argument    --user-data-dir=${PROFILE_DIR}
    ${driver}=    Create Webdriver    Chrome    options=${chrome_options}
    Go To    https://www.google.com
    Sleep    5s
    Close Browser
