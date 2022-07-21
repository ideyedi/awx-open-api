def cloud = "kubernetes"

def project             = "infracm"
def name                = "web-api"
def fullName            = "${project}/${name}"

def registry            = "wregistry.wemakeprice.com"
def registryUrl         = "https://${registry}"
def targetClusters      = "${targetClusterList}".split(',')    // BuildWithParameter 에서 정의됨
def deployable_branches = ["develop", "release/qa", "release/stg", "master"]

def label               = "${name}-${UUID.randomUUID().toString().toLowerCase()}"
def argocdServer        = "${argocdServer}"     // BuildWithParameter 에서 정의됨
def appWaitTimeout      = 600
def imageTag            = ""
def imageAlias          = ""

def BRANCH_TAG_MAP = [
  "develop":"develop",
  "release/qa":"qa",
  "stg":"staging",
  "staging":"staging",
  "release/stg":"staging",
  "release/staging":"staging",
  "master":"production",
  "main":"production"
]

podTemplate(
  cloud: cloud,
  label: label,
  imagePullSecrets: ["wregistry"],
  containers: [
    containerTemplate(
      name: "docker",
      image: "docker:17.09",
      ttyEnabled: true,
      command: "cat",
      args: ""
    ),
    containerTemplate(
      name: "argocd",
      image: "${registry}/infracm/argo-cd-cli:v1.7.2",
      ttyEnabled: true,
      command: "cat",
      args: ""
    )
  ],
  volumes: [
    hostPathVolume(
      hostPath: "/var/run/docker.sock",
      mountPath: "/var/run/docker.sock"
    )
  ]) {

  node(label) {
    def scmInfo = checkout scm
    def gitCommit = scmInfo.GIT_COMMIT.substring(0, 7)
    imageTag = gitCommit
    def branch = scmInfo.GIT_BRANCH.replaceAll("origin/", "")

    if (BRANCH_TAG_MAP.containsKey(branch)) {
      imageAlias = BRANCH_TAG_MAP[branch]
    }

    // exit gracefully if not the deployable branches
    if (!deployable_branches.contains(branch)) {
      stage("Skipping pipeline") {
        println "Branch: ${branch} is not part of deployable_branches"
        println "Skipping pipeline"
      }
      currentBuild.result = "SUCCESS"
      return
    }

    stage("Docker image Build & Push") {
      container('docker') {
        withDockerRegistry([credentialsId: "wregristy", url: "${registryUrl}"]) {
          sh "docker build --network=host -t $registry/$fullName:$gitCommit ."
          docker.image("$registry/$fullName:$gitCommit").push()
          if (imageAlias != "") {
            sh "docker tag $registry/$fullName:$gitCommit $registry/$fullName:$imageAlias"
            docker.image("$registry/$fullName:$imageAlias").push()
          }
        }
      }
    }

    stage("Deploying ${name}") {
      container('argocd') {
        withCredentials([string(credentialsId: "argocdAuthToken", variable: 'ARGOCD_AUTH_TOKEN')]) {
          def options = "--insecure --server ${argocdServer}"
          if (branch == "develop") {
            options = "$options --grpc-web"
          }
          for (int i = 0; i < targetClusters.size(); i++) {
            def appName = "${project}-${name}-${targetClusters[i]}"
            sh "/argocd app set ${appName} ${options} --helm-set image.tag=${imageTag}"
          }
        }
      }
    }
  }
}
