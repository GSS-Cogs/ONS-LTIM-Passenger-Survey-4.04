pipeline {
    agent {
        label 'master'
    }
    triggers {
        upstream(upstreamProjects: '../Reference/ref_migration',
                 threshold: hudson.model.Result.SUCCESS)
    }
    stages {
        stage('Clean') {
            steps {
                sh 'rm -rf out'
            }
        }
        stage('Transform') {
            agent {
                docker {
                    image 'cloudfluff/databaker'
                    reuseNode true
                }
            }
            steps {
                sh "jupyter-nbconvert --output-dir=out --ExecutePreprocessor.timeout=None --execute 'main.ipynb'"
            }
        }
        stage('Test') {
            agent {
                docker {
                    image 'cloudfluff/csvlint'
                    reuseNode true
                }
            }
            steps {
                script {
                    ansiColor('xterm') {
                        sh "csvlint -s schema.json"
                    }
                }
            }
        }
        stage('Upload draftset') {
            steps {
                script {
                    jobDraft.replace()
                    uploadTidy(['out/observations.csv'],
                               'https://github.com/ONS-OpenData/ref_migration/raw/master/columns.csv')
                }
            }
        }
        stage('Publish') {
            steps {
                script {
                    jobDraft.publish()
                }
            }
        }
    }
    post {
        always {
            script {
                archiveArtifacts 'out/*'

                configFileProvider([configFile(fileId: 'trello', variable: 'configfile')]) {
                    def config = readJSON(text: readFile(file: configfile))
                    String data = """{"idValue": "${config['results'][currentBuild.currentResult]}"}"""
                    def response = httpRequest(contentType: 'APPLICATION_JSON',
                      httpMode: 'PUT',
                      url: "https://api.trello.com/1/card/5b4728560fe67f87ff11202b/customField/${config['field']}/item?key=${config['key']}&token=${config['token']}",
                      requestBody: data
                    )
                }
            }
        }
        success {
            build job: '../GDP-tests', wait: false
        }
    }
}
