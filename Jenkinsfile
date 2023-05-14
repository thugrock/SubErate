pipeline{
    agent any

    stages{
        stage('SCM'){
            steps{
                git 'https://github.com/thugrock/SubErate.git'
            }
        }
        stage('Build requirements'){
            steps{
                sh 'pip install -r ./requirements.txt'
            }
        }
        stage('Docker Build') {
            steps {
      	        sh '  docker build -t thugrock/suberate:latest .'
            }
        }
        stage('Pushing image to Hub') {
            steps {
                withCredentials([usernamePassword(credentialsId: 'DockerHub', passwordVariable: 'dockerHubPassword', usernameVariable: 'dockerHubUser')]) {
                sh "docker login -u ${env.dockerHubUser} -p ${env.dockerHubPassword}"
                sh 'docker push thugrock/suberate:latest'
                }
            }
        }
        stage('Clean the Clients'){
            agent any
            steps{
                catchError(buildResult: "SUCCESS", stageResult: "SUCCESS") {
                    sh 'ansible-playbook  -i hosts clean_clients.yml'
                }
            }
        }
        stage('Deploy by Ansible'){
            steps{
                sh 'ansible-playbook -i hosts playbook.yml'
            }
        }
    }
}
