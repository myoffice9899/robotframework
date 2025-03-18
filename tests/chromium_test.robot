*** Settings ***
Library    SeleniumLibrary

*** Test Cases ***
Open Google
    Open Browser  https://www.google.com  gc
    Sleep    5s
    Capture Page Screenshot
    Close Browser
