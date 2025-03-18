*** Settings ***
Library    SeleniumLibrary

*** Test Cases ***
Open Google
    ${chrome_options}=    Evaluate    sys.modules['selenium.webdriver'].ChromeOptions()    sys
    Call Method    ${chrome_options}    add_argument    --headless
    Call Method    ${chrome_options}    add_argument    --no-sandbox
    Call Method    ${chrome_options}    add_argument    --disable-dev-shm-usage
    ${driver}=    Create Webdriver    Chrome    options=${chrome_options}
    Go To    https://www.google.com
    Sleep    5s
    Capture Page Screenshot
    Close Browser
