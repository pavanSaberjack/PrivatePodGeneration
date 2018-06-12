import os
import subprocess # just to call an arbitrary command e.g. 'ls'
import sys
import shutil

try:
    # for Python2
    from  Tkinter import *
    import Tkinter, Tkconstants, tkFileDialog
except ImportError:
    # for Python 3    
    from tkinter import filedialog

# Sample class for navigation
class cd:
    """Context manager for changing the current working directory"""
    def __init__(self, newPath):
        self.newPath = os.path.expanduser(newPath)

    def __enter__(self):
        self.savedPath = os.getcwd()
        os.chdir(self.newPath)

    def __exit__(self, etype, value, traceback):
        os.chdir(self.savedPath)
    
## Helper functions
def get_user_input(message):
    ''' (str) -> str

    Get the input from the user in the form of string depending on the python version
    '''
    if sys.version_info[0] < 3:
        
        return raw_input(message)
    else:
        return str(input(message))

def run_command(command):
    '''
        (str) -> Bool

        Returns True if the command is executed successfully
    '''
    retcode = subprocess.call(command)
    if retcode == 0:
        print("--- Command success \n")
        return True
    else:
        print("Something went wrong: " + retcode)
        return False

def get_directory_path():
    ''' () -> str

        Asks user to select a directory and returns selected path
    '''
    # Manage python version 
    if sys.version_info[0] < 3:
        root = Tk()
        root.title('Select folder to clone your framework')
        root.directory = tkFileDialog.askdirectory()
        return root.directory
    else:
        return filedialog.askdirectory()

def get_command_list(command):
    ''' (str) -> [str]

        Returns the list of strings for a given command
    '''
    return command.split(' ')


# Main functions
def generate_cocoapods():
    ''' () -> ()

        Start of the process, call this function to start the cocoapod generation
    
    '''
    # Create pod spec repo
    print("\n\n####### Creating pods #######\n\n")
    create_pod_spec_repo()

    # Create pod repo
    create_pod_repo()

def create_pod_spec_repo():
    ''' () -> ()

    Navigates to ~/.cocoapods/repos/ adds local repo with pod_spec_repo_name collected from user
    '''
    directory_path = "~/.cocoapods/repos/" # Cocoapods directory path
    with cd(directory_path):
        print("------ Navigating to the cocoapods directory --------\n")
        
        # we are in cocoapods directory
        print("--- Creating your local pod repo \n ")
        pod_repo_add_command = ["pod", "repo", "add", pod_spec_repo_name, pod_spec_repo_url]

        if run_command(pod_repo_add_command) == True:
            # Validate pod spec repo
            validate_pod_spec_repo(directory_path)
        

def validate_pod_spec_repo(directory_path):
    '''  (str) -> ()

    Validates the local pod created in directory_path
    '''
    print("--- Validating your repo \n")

    # Navigate inside the locally created spec repo
    directory_path = directory_path + '/' + pod_spec_repo_name
    print(directory_path)
    with cd(directory_path):
        lint_cmd = ['pod', 'repo', 'lint', '.']
        run_command(lint_cmd)

def create_pod_repo():
    #select the path to clone the repository
    print("-- Select a folder to clone your directory")
    folder_path = get_directory_path()

    # Navigate to pod folder 
    with cd(folder_path):
        # Clone the pod to the selected folder
        cmd = ['git', 'clone', custom_pod_repo_url]
        if run_command(cmd) == True:
            folder_path = folder_path + '/' + custom_pod_name
            with cd(folder_path):
                create_pod_library(folder_path)

def create_pod_library(folder_path):
    # Create pod library
    cmd = ['pod', 'lib', 'create', custom_pod_name]

    if run_command(cmd) == True:
        move_files_from_parent_directory_to_root_directory(folder_path)


def move_files_from_parent_directory_to_root_directory(folder_path):
    # Rename the folder for easy work-around
    # adding _tmp_automate for now
    path = folder_path + '/' + custom_pod_name # get the folder name
    os.rename(path, path + '_tmp_automate') # rename it by adding _tmp_automate as suffix
    
    # Navigate to Pod folder and delete .git file
    updated_pod_name = custom_pod_name + '_tmp_automate'
    cwd = folder_path + '/' + updated_pod_name 
    
    with cd(cwd):
        remove_git_file_cmd = ['rm', '-rf', '.git'] # Remove the .git file as there will be two .git files in root and parent
        run_command(remove_git_file_cmd)

        # Move all the files to root folder
        source = os.listdir(cwd)
        destination = folder_path

        for file in source:
            if file == '.DS_Store':
                continue
                
            if file == '.git':
                continue
                
            file_path = cwd + '/' + file
            if file_path != destination:
                shutil.move(file_path, destination)
                    
    # Delete the empty folder    
    shutil.rmtree(cwd)

    # Update the pod spec file
    update_pod_spec_file(path + '.podspec' )

    # Run the command
    print("--- Linting your pod")
    lint_command = ["pod", "lib", "lint", custom_pod_name + '.podspec']

    if run_command(lint_command) ==  True:
        #Wait for user input to continue
        response = get_user_input('Do you want to continue the process (y/n): ')

        install_pods_in_example_project(folder_path)

        response = get_user_input('Do you want to continue the process (y/n): ')

        push_code_to_remote()

        push_to_spec_repo()
        

def push_code_to_remote():
    print("--- Adding it to git repo")
    cmd = ["git", "add", "."]
    run_command(cmd)
    
    cmd = ["git", "add", "--all"]
    run_command(cmd)

    commit_message = get_user_input('Enter you commit message: ')
    cmd = ["git", "commit", "-m", commit_message]
    run_command(cmd)

    cmd = ["git", "push", "origin", "master"]
    run_command(cmd)

    tag_no = get_user_input('Enter you tag no: ')
    cmd = ["git", "tag", tag_no]
    run_command(cmd)

    cmd = ["git", "push", "--tags"]
    run_command(cmd)

def push_to_spec_repo():

    print("--- Validating before pushing code to spec repo")
    cmd = ["pod", "spec", "lint", custom_pod_name + '.podspec']
    run_command(cmd)
        
    print("--- Pushing code to spec repo")
    cmd = ["pod", "repo", "push", pod_spec_repo_name, custom_pod_name + '.podspec']
    run_command(cmd)

def install_pods_in_example_project(folder_path):
    example_project_directory = folder_path + '/Example'
    with cd(example_project_directory):
        print("--- Installing your pods")
        cmd = ["pod", "install"]
        run_command(cmd)

def update_pod_spec_file(file_path):
    '''
        (str) -> ()

        Reads the pod spec file and asks user for data where needed and updates the file
    '''

    # Open podspec file
    f = open(file_path, 'r')

    # Read all the contents
    contents = f.readlines()

    # Close the file
    f.close()

    # Buffer to store the updated content
    updated_contents = []

    # Loop through each line of the file and ask user for inputs when needed
    for line_index in range(len(contents)):

        # Get the line
        line = contents[line_index]

        # Strip white spaces on both sides
        line = line.strip()

        # Create the line as array for checking user imputs
        array = line.split(" ")

        # If empty line or just a new line just add it for better indentaion
        if len(array) == 0:
            updated_contents.append(line)
            continue

        # Access the value
        val = array[0]

        # Ask user for summary 
        if val == 's.summary':
            summary = get_user_input('Enter summary: ')
            line = val + '    = \'' + summary + '\''
            updated_contents.append(line)
            continue

        # Ask user for description of the pod 
        if val == 's.description':
            description = get_user_input('Enter Description: ')
            updated_contents.append(line)
            updated_contents.append(description)
            # updated_contents.append('DESC')
            #line_index = line_index + 3
            continue

        # Home page url to be updated
        if val == 's.homepage':
            home_page_url = get_user_input('Enter bitbucket home page url: ')
            line = val + '    = \'' + home_page_url + '\''
            updated_contents.append(line)
            continue

        # Souce code url
        if val == 's.source':
            bitbucket_source_url = get_user_input('Enter bitbucket source url: ')
            line = val + '    = { :git => \'' + bitbucket_source_url + '\', :tag => s.version.to_s }'
            updated_contents.append(line)
            continue

        # End of the file reached so adding required lines
        if val == 'end':
            updated_contents.append('\n')
            updated_contents.append('s.platform = :ios, \"9.0\"')
            updated_contents.append('s.pod_target_xcconfig = { \'SWIFT_VERSION\' => \'4.0\' }')
            updated_contents.append('`echo "4.0" > .swift-version`')
            updated_contents.append(line)
            continue

        updated_contents.append(line)

    # Open the same file again and add the lines with new line characters at the end
    f = open(file_path, 'w')
    for line in updated_contents:
        f.write(line + '\n')
    f.close()


# Fetch all the required data at one go
pod_spec_repo_name = get_user_input("Enter your Pod Spec Repo Name: ")
pod_spec_repo_url = get_user_input("Enter Pod Spec Repo URL: ")
custom_pod_repo_url = get_user_input("Enter Pod repo url: ")
custom_pod_name = get_user_input("Enter your custom Pod name : ")

generate_cocoapods()
